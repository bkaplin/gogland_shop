import logging
from datetime import datetime, timedelta

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from django.conf import settings

from bot.models import Chat, CardNumber, ShopSettings, Message, GroupBotMessage
from order.choices import PayType
from order.models import Order, OrderItem
from product.models import Category, Product
from user.models import User

# Ведение журнала логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def dotval(obj, attr, default=None):
    return getattr(obj, attr) if hasattr(obj, attr) else default


class BotService:

    def __init__(self):
        self.bot = telegram.Bot(token=settings.TG_TOKEN)
        self.cart_number = CardNumber.objects.filter(is_active=True).first()
        self.cart_info_message = f"Оплатить по номеру карты \n\n" \
                                 f"`{self.cart_number.number}`\n" \
                                 f"(нажать, чтобы скопировать)." if self.cart_number else ""
        self.work_time_text_fmt = '❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗\nВремя работы магазина {}\n❗❗❗❗❗❗❗❗❗❗❗❗❗❗❗\n'

    @staticmethod
    def _get_local_user(tg_user):
        user_id = dotval(tg_user, 'id')
        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user:
            local_user, created = User.objects.get_or_create(
                tg_id=user_id,
                last_name=dotval(tg_user, 'last_name'),
                first_name=dotval(tg_user, 'first_name'),
                username=dotval(tg_user, 'username')
            )
        return local_user, user_id

    @staticmethod
    def _get_local_chat(user):
        local_chat = Chat.objects.filter(tg_id=user.tg_id).first()
        if not local_chat:
            local_chat = Chat.objects.create(
                user=user,
                tg_id=user.tg_id
            )
        return local_chat

    def _process_order_status(self, variant, query, local_user):
        order_id = variant.split('-')[-1]

        # берем текст сообщения минус последний символ, в котором значок ⚠
        answer_text = '\n'.join(query.message.text.split('\n')[:-1]) + '\n'
        _order_reply_markup_for_admin = None
        if order_id:
            _order = Order.objects.filter(id=order_id).first()
            help_text_for_admin = 'Детали в админке'
            icon_for_user = ''
            if _order and (local_user.is_admin or local_user == _order.user):
                if variant.startswith('__shipped'):
                    _order.set_shipped()
                    if not _order.is_payed:
                        answer_text += settings.SHIPPED_ICON
                        icon_for_user = settings.SHIPPED_ICON
                    else:
                        answer_text += settings.PAYED_ICON
                        if _order.pay_type == PayType.CARD:
                            answer_text += settings.CARD_ICON
                        elif _order.pay_type == PayType.CASH:
                            answer_text += settings.CASH_ICON
                        icon_for_user = settings.PAYED_ICON

                    _order_buttons_for_admin = self.get_order_buttons(
                        order_id,
                        shipped_btn=False,
                        payed_btn=(not _order.is_closed),
                        cancel_btn=(not _order.is_closed),
                    )
                    _order_reply_markup_for_admin = InlineKeyboardMarkup(_order_buttons_for_admin)

                    logger.info(f"Заказ {order_id} вручен")

                elif variant.startswith('__payed'):
                    if not _order.cancelled:
                        result_icon = settings.PAYED_ICON
                        if not _order.is_payed:
                            _order.set_payed()
                            if variant.startswith('__payed_card'):
                                _order.set_pay_type_card()
                                result_icon += settings.CARD_ICON
                            elif variant.startswith('__payed_cash'):
                                _order.set_pay_type_cash()
                                result_icon += settings.CASH_ICON
                        answer_text += result_icon
                    else:
                        answer_text += f'{settings.CANCELLED_ICON} Уже было отменено\n{help_text_for_admin}'
                    icon_for_user = settings.PAYED_ICON

                    _order_buttons_for_admin = self.get_order_buttons(
                        order_id,
                        shipped_btn=(not _order.shipped),
                        payed_btn=False,
                        cancel_btn=False,
                    )
                    _order_reply_markup_for_admin = InlineKeyboardMarkup(_order_buttons_for_admin)

                    logger.info(f"Заказ {order_id} оплачен")

                elif variant.startswith('__cancel'):
                    if not _order.is_payed:
                        if not _order.cancelled:
                            _order.cancel_order_n_recalculate_rests()
                        answer_text += settings.CANCELLED_ICON
                    else:
                        answer_text += f'{settings.PAYED_ICON} Уже было оплачено\n{help_text_for_admin}'
                    icon_for_user = settings.CANCELLED_ICON

                    _order_reply_markup_for_admin = None

                    logger.info(f"Заказ {order_id} отменен")

                    # если заказ отменил покупатель, то удаляем сообщения в админских чатах об этом заказе
                    if local_user == _order.user and not local_user.is_admin:
                        _order.comment = f'{_order.comment or ""}\nОтменен покупателем'
                        _order.save(update_fields=['comment'])
                        _order_messages = _order.messages.filter(is_for_admins=True)
                        for _order_message in _order_messages:
                            new_message_text = f'{_order_message.text[:-1]}\n{settings.CANCELLED_ICON} (Отменено покупателем)'
                            if _order_message.chat:
                                self.bot.edit_message_text(
                                    chat_id=_order_message.chat.tg_id,
                                    message_id=_order_message.message_id,
                                    text=new_message_text,
                                    parse_mode=telegram.ParseMode.MARKDOWN
                                )

                # убираем кнопку отмены у пользователя после оплаты или отмены от админа
                if local_user.is_admin:
                    user_order_messages = _order.messages.filter(is_for_admins=False)
                    for user_mes in user_order_messages:
                        if user_mes.chat:
                            try:
                                self.bot.edit_message_text(
                                    chat_id=user_mes.chat.tg_id,
                                    message_id=user_mes.message_id,
                                    text=f'{user_mes.text}\n{icon_for_user}',
                                    parse_mode=telegram.ParseMode.MARKDOWN,
                                    reply_markup=None
                                )
                            except:
                                pass

        # если пользователь не админ, то кнопок в ответе быть не может
        if not local_user.is_admin:
            _order_reply_markup_for_admin = None

        query.answer()
        query.edit_message_text(text=answer_text, reply_markup=_order_reply_markup_for_admin)
        return

    @staticmethod
    def _cancel_order_and_exit(query, tg_user, order):
        if order:
            order.cancel_order_n_recalculate_rests()
            logger.info(f"Пользователь {tg_user.id}:{tg_user.first_name} отменил заказ №{order.pk}")

        query.edit_message_text(text="Приходите еще")

        logger.info(f"Пользователь {tg_user.id}:{tg_user.first_name} вышел")
        return ConversationHandler.END

    def _send_notification_to_admins(self, order):
        """отправка сообщений в чаты админов о новом заказе"""
        order_buttons_for_admin = self.get_order_buttons(order.id)
        order_reply_markup_for_admin = InlineKeyboardMarkup(order_buttons_for_admin)

        message_to_admins = f"Сделан заказ №{order.pk} на {order.total_int} ₽ от {order.user}\n\n{order.info}{settings.WARNING_ICON}"
        self._send_message_to_admins_chats(message_to_admins, reply_markup=order_reply_markup_for_admin, order=order)

    def _send_message_to_admins_chats(self, message_to_admins, reply_markup=None, order=None):
        admins_chats = Chat.objects.filter(is_admins_chat=True)
        for admin_chat in admins_chats:
            tg_message = self.bot.send_message(
                text=message_to_admins,
                chat_id=admin_chat.tg_id,
                reply_markup=reply_markup
            )
            Message.objects.create(
                chat=admin_chat,
                text=message_to_admins,
                message_id=tg_message.message_id,
                order=order,
                is_for_admins=True,
            )

    def _send_notification_to_user(self, query, order, local_chat):
        """отправляем сообщение покупателю и создаем сообщение"""
        shop_settings = ShopSettings.get_solo()
        shop_start_work, shop_end_work = shop_settings.work_start, shop_settings.work_end

        order_buttons_for_user = self.get_cancel_order_button(order.id)
        order_reply_markup_for_user = InlineKeyboardMarkup(order_buttons_for_user)
        message_to_user = f"Заказ оформлен.\n{order.info}{self.cart_info_message}"
        query.edit_message_text(
            text=message_to_user,
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=order_reply_markup_for_user
        )

        now_time = datetime.now().time()
        if now_time < shop_start_work or now_time > shop_end_work:
            warning_text = f'{self.work_time_text_fmt.format(shop_settings.work_time_today)}\n' \
                           f'Сейчас заказ не будет выдан. Приходите в рабочее время.'
            self.bot.send_message(
                text=warning_text, chat_id=local_chat.tg_id
            )

        Message.objects.create(
            chat=local_chat,
            text=message_to_user,
            message_id=query.message.message_id,
            order_id=order.pk,
        )

    def _confirm_order(self, query, order, tg_user, local_chat):
        order.in_cart = False
        order.update_sum()
        order.recalculate_rests()

        logger.info(f"Пользователь {tg_user.id}:{tg_user.first_name} оформил заказ №{order.pk} на {order.total_int} ₽")

        self._send_notification_to_admins(order)
        self._send_notification_to_user(query, order, local_chat)

        return

    def _create_order_item_in_cart(self, query, product, local_user):
        query.edit_message_text(text=f'Сколько нужно "{product.name}"? Отправьте количество.\n(0 - для отмены)')
        order, o_created = Order.objects.get_or_create(
            user=local_user, in_cart=True
        )
        OrderItem.objects.filter(order=order, count__lt=1).delete()
        oi, oi_created = OrderItem.objects.get_or_create(
            product=product,
            order=order,
        )
        oi.in_process = True
        oi.save()
        return

    def _process_order_item_count(self, update, text_received, local_user, tg_user):
        work_time = ShopSettings.get_solo().work_time_today
        work_time_text = self.work_time_text_fmt.format(work_time)

        order = local_user.orders.filter(in_cart=True).first()
        oi = order.items.filter(in_process=True).first()
        oi_category = oi.product.category
        if not oi:
            return
        count = float(text_received)
        if count == 0:
            oi.delete()
            additional_message = f'{order.info}'

            buttons = self.get_buttons(oi_category, True and order.items.exists(), user_tg_id=tg_user.id)
            reply_markup = InlineKeyboardMarkup(buttons)
            update.message.reply_text(
                text=f"{work_time_text}\n{additional_message}{oi_category.name if oi_category else 'Выберете товар'}",
                reply_markup=reply_markup)
            return
        if count < 0:
            raise Exception
        valid_count = count if count <= oi.product.rest else oi.product.rest
        oi.count += valid_count
        oi.in_process = False
        oi.save()

        logger.info(f"Пользователь {tg_user.id}:{tg_user.first_name} добавил продукт {oi.product.pk}:{oi.product.name} в количестве {valid_count} шт. на сумму {oi.product.price_with_coupon() * valid_count} ₽")

        max_count = count >= oi.product.rest
        oi.reduce_rest(valid_count)
        order.update_sum()

        max_count_message = "(Максимальное количество)" if max_count else ""
        additional_message = f'Добавлен товар {oi.product.name} в количестве {int(oi.count)}шт.{max_count_message} на {oi.sum_int} ₽\n\n{order.info}'

        buttons = self.get_buttons(oi_category, True and order.items.exists(), user_tg_id=tg_user.id)
        reply_markup = InlineKeyboardMarkup(buttons)

        update.message.reply_text(
            text=f"{work_time_text}\n{additional_message}{oi_category.name if oi_category else 'Выберете товар'}",
            reply_markup=reply_markup)

    def _add_comment_to_order(self, text_received, local_user):
        text_list = [t for t in text_received.replace('  ', ' ').split(' ') if t]
        if len(text_list) >= 3:
            _order_id, _comment = text_list[1], ' '.join(text_list[2:])
            _order = Order.objects.filter(id=_order_id).first()
            if _order:
                _order.comment = _comment
                _order.save(update_fields=['comment'])

                logger.info(f"Добавлен комментарий к заказу {_order_id}")
                message = f'Комментарий к заказу {_order_id} добавлен'
            else:
                message = f'Нет заказа {_order_id}'
        else:
            message = 'Не хватает информации, чтобы добавить комментарий'

        self.bot.send_message(chat_id=local_user.tg_id, text=message)

        return

    def _add_message_to_order_user(self, text_received, local_user):
        text_list = [t for t in text_received.replace('  ', ' ').split(' ') if t]
        if len(text_list) >= 3:
            _order_id, _message = text_list[1], ' '.join(text_list[2:])
            _order = Order.objects.filter(id=_order_id).first()
            if _order:
                order_user = _order.user
                if order_user and order_user.tg_id:
                    self.bot.send_message(chat_id=order_user.tg_id,
                                          text=f"Привет. Уточнения по заказу {_order_id}.\n{_message}")

                logger.info(f"Отправлено сообщение пользователю {order_user} (id:{order_user.tg_id}) заказа {_order_id}")
                admin_message = f'Сообщение к заказу {_order_id} отправлено {order_user}'
            else:
                admin_message = f'Нет заказа {_order_id}'
        else:
            admin_message = 'Не хватает информации, чтобы отправить сообщение'

        self.bot.send_message(chat_id=local_user.tg_id, text=admin_message)

        return

    def _add_global_message_to_order_user(self, text_received, local_user):
        text_list = [t for t in text_received.replace('  ', ' ').split(' ') if t]
        if len(text_list) >= 2:
            _message = ' '.join(text_list[1:])
            group_message = GroupBotMessage.objects.create(message_text=_message)

            all_active_users = User.objects.filter(is_active=True, is_verified=True)
            group_message.users.add(*list(all_active_users.values_list('id', flat=True)))

            group_message.send()

            admin_message_list = ['Сообщение отправлено:']
            admin_message_list.append(group_message.log)
            admin_message = '\n'.join(admin_message_list)

            logger.info(f"Отправлено глобальное сообщение пользователям\n{group_message.log}")
        else:
            admin_message = 'Не хватает информации, чтобы отправить сообщение'

        self.bot.send_message(chat_id=local_user.tg_id, text=admin_message)

        return

    def check_admin_user(self, update, check_super_admin=False):
        user = update.message.from_user
        user_id = dotval(user, 'id')
        if settings.CORRECT_USERS and str(user_id) not in settings.CORRECT_USERS:
            raise Exception

        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user or not local_user.is_admin:
            raise Exception
        if check_super_admin and str(user_id) not in settings.SUPER_ADMINS_IDS:
            raise Exception

    def _init_admins_chat(self, update, _):
        """Вызывается по команде `/_init_admins_chat`."""
        self.check_admin_user(update)

        chat_id = update.message.chat_id

        admins_chat, chat_created = Chat.objects.get_or_create(
            tg_id=chat_id,
        )
        admins_chat.is_admins_chat = True
        admins_chat.save(update_fields=['is_admins_chat'])

        logger.info(f"Чат админов зарегистрирован: {chat_id}")
        self.bot.send_message(chat_id=admins_chat.tg_id, text="Чат админов зарегистрирован. "
                                                              "Теперь тут будут присылаться оповещания о заказах")
        return

    def _delete_admins_chat(self, update, _):
        """Вызывается по команде `/_init_admins_chat`."""
        self.check_admin_user(update)

        chat_id = update.message.chat_id

        admins_chat = Chat.objects.filter(tg_id=chat_id, is_admins_chat=True).first()
        if admins_chat:
            admins_chat.is_admins_chat = False
            admins_chat.save(update_fields=['is_admins_chat'])
            logger.info(f"Чат админов удалён: {chat_id}")
            self.bot.send_message(chat_id=admins_chat.tg_id, text="Чат админов удалён. "
                                                                  "Теперь тут НЕ будут присылаться оповещания о заказах")
        return

    def _debts(self, update, _):
        self.check_admin_user(update)

        debt_dict = self.get_debt_dict()

        res_message = '\n'.join(
            [f'{owner}: {total_debt} ₽' for owner, total_debt in debt_dict.items()]) if debt_dict else 'Нет долгов'

        chat_id = update.message.chat_id

        chat = Chat.objects.filter(tg_id=chat_id).first()
        if chat:
            self.bot.send_message(chat_id=chat.tg_id, text=res_message)

    def _bot_off(self, update, _):
        message_to_admins = 'Бот временно отключен. Доступ к функционалу имеют только суперадмины.'
        self._change_bot_work(update, True, message_to_admins)

    def _bot_on(self, update, _):
        message_to_admins = 'Бот включен. Все имеют доступ к функционалу бота.'
        self._change_bot_work(update, False, message_to_admins)

    def _change_bot_work(self, update, disable, message_to_admins):
        self.check_admin_user(update, check_super_admin=True)
        bot_settings = ShopSettings.get_solo()
        bot_settings.disable_bot = disable
        bot_settings.save()

        self._send_message_to_admins_chats(message_to_admins)

    def get_debt_dict(self, user=None, full_info=False):
        tomorrow = datetime.today() + timedelta(days=1)
        not_payed_orders = Order.objects.filter(
            is_payed=False,
            in_cart=False,
            shipped=True,
            cancelled=False,
            created__range=[settings.START_SHOW_ORDER_DEBTS, tomorrow.strftime('%Y-%m-%d')],
        )
        if user:
            not_payed_orders = not_payed_orders.filter(user=user)

        res_dict = {}

        for order in not_payed_orders:
            owner = str(order.user)

            if full_info and user:
                if owner not in res_dict:
                    res_dict[owner] = []
                res_dict[owner].append(f'Заказ №{order.id}: {order.total_int} ₽')
            else:
                if owner not in res_dict:
                    res_dict[owner] = 0
                res_dict[owner] += order.total_int

        return res_dict

    def _get_debt_for_order_user(self, text_received, local_user):
        text_list = [t for t in text_received.replace('  ', ' ').split(' ') if t]
        if len(text_list) == 2:
            _order_id = text_list[1]
            _order = Order.objects.filter(id=_order_id).first()
            if _order:
                order_user = _order.user
                if order_user and order_user.tg_id:
                    user_debt_dict = self.get_debt_dict(user=order_user, full_info=True)
                    orders_info = '\n'.join(user_debt_dict[str(order_user)]) if user_debt_dict else 'Нет долгов'
                    admin_message = f'{order_user}:\n{orders_info}'
                else:
                    admin_message = f'У заказа {_order_id} нет пользователя'
            else:
                admin_message = f'Нет заказа {_order_id}'
        else:
            admin_message = 'Не хватает информации, чтобы отправить сообщение'

        self.bot.send_message(chat_id=local_user.tg_id, text=admin_message)

        return

    def check_disable_bot(self, user_id):
        # если бот выключен, сообщим об этом
        if ShopSettings.get_solo().disable_bot and str(user_id) not in settings.SUPER_ADMINS_IDS:
            self.bot.send_message(
                text=f"Бот временно недоступен",
                chat_id=user_id,
            )
            return True
        return False

    def start(self, update, _):
        """Вызывается по команде `/start`."""
        bot_settings = ShopSettings.get_solo()

        # Получаем пользователя, который запустил команду `/start`
        user = update.message.from_user
        user_id = dotval(user, 'id')
        if settings.CORRECT_USERS and str(user_id) not in settings.CORRECT_USERS:
            raise Exception

        local_user, user_id = self._get_local_user(user)
        local_chat = self._get_local_chat(local_user)

        logger.info(f"Пользователь {user_id}:{user.first_name} зашел")

        # если выключена верификация, то пропускаем любого пользователя и даем делать заказ
        enable_verification = bot_settings.enable_verification
        if not enable_verification:
            local_user.is_verified = True
            local_user.save()

        # не даем ничего не верифицированному пользователю и сообщаем админам
        if not local_user.is_verified:
            update.message.reply_text(
                text=f"Обратитесь к разработчику за уточнениями",
            )

            admins_chats = Chat.objects.filter(is_admins_chat=True)
            message_to_admins = f"Не верифицированный пользователь пытается сделать заказ.\n{local_user}: {user_id}"
            has_notification_to_admin = Message.objects.filter(chat__in=admins_chats,
                                                               text=message_to_admins,
                                                               is_for_admins=True).exists()
            if not has_notification_to_admin:
                for admin_chat in admins_chats:
                    tg_message = self.bot.send_message(
                        text=message_to_admins,
                        chat_id=admin_chat.tg_id,
                    )
                    Message.objects.create(
                        chat=admin_chat,
                        text=message_to_admins,
                        message_id=tg_message.message_id,
                        is_for_admins=True,
                    )
            return

        # если бот выключен, сообщим об этом и выкинем
        if self.check_disable_bot(user_id):
            return

        orders_in_cart = local_user.orders.filter(in_cart=True)
        for order in orders_in_cart:
            order.cancel_order_n_recalculate_rests()

        # # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
        self.send_root_menu(update, False)

    def send_root_menu(self, update, user_has_order_in_cart, additional_message=''):
        keyboard = self.get_root_menu(user_has_order_in_cart)
        reply_markup = InlineKeyboardMarkup(keyboard)

        work_time = ShopSettings.get_solo().work_time_today
        work_time_text = self.work_time_text_fmt.format(work_time)

        # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
        update.message.reply_text(
            text=f"{work_time_text}\n{additional_message}Выберите товар", reply_markup=reply_markup
        )

    def get_order_buttons(self, order_id, shipped_btn=True, payed_btn=True, cancel_btn=True):
        l, bottom_buttons = [], []
        if shipped_btn:
            l.append([InlineKeyboardButton(f"Вручено {settings.SHIPPED_ICON}", callback_data=str(f'__shipped-{order_id}'))])
        if payed_btn:
            bottom_buttons.append(
                InlineKeyboardButton(f"Карта {settings.CARD_ICON}", callback_data=str(f'__payed_card-{order_id}')))
            bottom_buttons.append(
                InlineKeyboardButton(f"Нал {settings.CASH_ICON}", callback_data=str(f'__payed_cash-{order_id}')))
        l.append(bottom_buttons)
        if cancel_btn:
            l.append([
                InlineKeyboardButton(f"Отменить {settings.CANCELLED_ICON}", callback_data=str(f'__cancel-{order_id}'))
            ])

        return l

    def get_cancel_order_button(self, order_id):
        bottom_buttons = []
        bottom_buttons.append(InlineKeyboardButton(f"Отменить {settings.CANCELLED_ICON}", callback_data=str(f'__cancel-{order_id}')))
        return [bottom_buttons]

    def get_root_menu(self, user_has_order_in_cart, user_tg_id=None):
        l = [[InlineKeyboardButton(c.name, callback_data=str(c.pk))] for c in Category.objects.filter(parent__isnull=True).order_by('position') if c.has_products(user_tg_id)]

        bottom_buttons = []
        if user_has_order_in_cart:
            bottom_buttons.append(InlineKeyboardButton(f"Оформить {settings.PAYED_ICON}", callback_data=str('confirm')))
        bottom_buttons.append(InlineKeyboardButton(f"Отмена {settings.CANCELLED_ICON}", callback_data=str('exit')))
        l.append(bottom_buttons)
        return l

    def get_buttons(self, category, user_has_order_in_cart, user_tg_id=None):
        if not category:
            return
        childs_categories = category.child_categories.order_by('position')
        category_products = category.products.filter(rest__gt=0, is_active=True)
        VIP_USERS_TG_IDS = set(list(User.objects.filter(is_vip=True).values_list('tg_id', flat=True)))
        ADMIN_USERS_TG_IDS = set(list(User.objects.filter(is_admin=True).values_list('tg_id', flat=True)))

        if user_tg_id and str(user_tg_id) in VIP_USERS_TG_IDS:
            category_products = category.products.filter(rest__gt=0)

        # если не суперадмин, то скрываем, если скрыт для всех.
        # суперадмин видит абсолютно все продукты в наличии
        if str(user_tg_id) not in settings.SUPER_ADMINS_IDS:
            category_products = category_products.exclude(hidden_for_all=True)

        bottom_buttons = []
        if childs_categories.exists():
            l = [[InlineKeyboardButton(c.name, callback_data=str(c.pk))] for c in childs_categories if c.has_products(user_tg_id)]
        else:
            l = [[InlineKeyboardButton(
                f'{p._menu_label}{p.name} {p.price_with_coupon()} ₽ '
                f'(Ост. {p.rest if p.rest <= 10 or (user_tg_id and str(user_tg_id) in ADMIN_USERS_TG_IDS) else ">10"})',
                callback_data=f'buy{p.pk}')] for p in category_products]

        if user_has_order_in_cart:
            bottom_buttons.append(InlineKeyboardButton(f"Оформить {settings.PAYED_ICON}", callback_data=str('confirm')))
        bottom_buttons += [
            InlineKeyboardButton(f"Отмена {settings.CANCELLED_ICON}", callback_data=str('exit')),
            InlineKeyboardButton(f"Назад {settings.BACK_ICON}", callback_data='back_to' + str(category.parent.pk if category.parent else '')),
        ]
        l.append(bottom_buttons)

        return l

    def button(self, update, _):
        query = update.callback_query
        variant = query.data

        user = query.from_user

        local_user, user_id = self._get_local_user(user)
        local_chat = self._get_local_chat(local_user)

        # если бот выключен, сообщим об этом и выкинем
        if self.check_disable_bot(user_id):
            return

        # если идет работа над заказом со стороны админа (оплачено/отменено)
        if variant.startswith('__'):
            return self._process_order_status(variant, query, local_user)

        work_time = ShopSettings.get_solo().work_time_today
        work_time_text = self.work_time_text_fmt.format(work_time)

        buy = False
        order = local_user.orders.filter(in_cart=True).first()
        additional_message = order.info if order else ''

        if variant.startswith('back_to'):
            variant = variant.replace('back_to', '')
        elif variant == 'exit':
            return self._cancel_order_and_exit(query, user, order)
        elif variant == 'confirm' and order:
            return self._confirm_order(query, order, user, local_chat)
        elif variant == 'confirm' and not order:
            # это происходит в случае, если чувак создал корзину и забыл,
            # а заказ уже отменен через админку, но он жмет кнопку оформить
            variant = None
        elif variant.startswith('buy'):
            variant = variant.replace('buy', '')
            buy = True

        if buy:
            product = Product.objects.filter(pk=variant).first()
            if product:
                return self._create_order_item_in_cart(query, product, local_user)

        category = None
        user_has_order_in_cart = local_user.orders.filter(in_cart=True, items__isnull=False).exclude(items__count__lt=1).exists()
        if variant:
            category = Category.objects.filter(pk=variant).first()
            buttons = self.get_buttons(category, user_has_order_in_cart, user_tg_id=user_id)
        else:
            buttons = self.get_root_menu(user_has_order_in_cart)
        reply_markup = InlineKeyboardMarkup(buttons)

        # `CallbackQueries` требует ответа, даже если уведомление для пользователя не требуется, в противном случае
        # у некоторых клиентов могут возникнуть проблемы. смотри https://core.telegram.org/bots/api#callbackquery.
        query.answer()

        # редактируем сообщение, тем самым кнопки в чате заменятся на этот ответ.
        query.edit_message_text(text=f"{work_time_text}\n{additional_message}{category.name if category else 'Выберете товар'}", reply_markup=reply_markup)

    @staticmethod
    def help_command(update, _):
        user = update.message.from_user
        user_id = dotval(user, 'id')
        local_user = User.objects.filter(tg_id=user_id).first()
        if local_user and local_user.is_admin:
            message = '/_init_admins_chat - для инициализации этого чата как админского\n' \
                      '/_delete_admins_chat - для удаления этого чата из админских\n' \
                      '/_debts - покажет всех должников с суммами\n' \
                      '/_bot_off - выключит бот\n' \
                      '/_bot_on - включит бот\n' \
                      'debt {order_id} - покажет все долги пользователя заказа order_id\n' \
                      'message {order_id} text - для отправки сообщения text пользователю заказа order_id\n' \
                      'comment {order_id} text - для добавления комментария text к заказу order_id\n' \
                      'globalmessage text - для отправки сообщения text всем активным пользователям бота\n' \
                      ''
        else:
            message = "Используйте `/start` для тестирования."
        update.message.reply_text(message)

    @staticmethod
    def error(update, context):
        update.message.reply_text('Что-то пошло не так. Отправьте корректный выбор.')

    def text(self, update, context):
        text_received = update.message.text
        user = update.message.from_user
        user_id = dotval(user, 'id')
        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user:
            return

        # если бот выключен, сообщим об этом и выкинем
        if self.check_disable_bot(user_id):
            return

        if text_received.lower().startswith('comment') and local_user.is_admin:
            return self._add_comment_to_order(text_received, local_user)

        if text_received.lower().startswith('message') and local_user.is_admin:
            return self._add_message_to_order_user(text_received, local_user)

        if text_received.lower().startswith('globalmessage') and local_user.is_admin:
            return self._add_global_message_to_order_user(text_received, local_user)

        if text_received.lower().startswith('debt') and local_user.is_admin:
            return self._get_debt_for_order_user(text_received, local_user)

        return self._process_order_item_count(update, text_received, local_user, user)

    def main(self):
        updater = Updater(settings.TG_TOKEN)
        dispatcher = updater.dispatcher

        updater.dispatcher.add_handler(CommandHandler('start', self.start))
        updater.dispatcher.add_handler(CommandHandler('_init_admins_chat', self._init_admins_chat))
        updater.dispatcher.add_handler(CommandHandler('_delete_admins_chat', self._delete_admins_chat))
        updater.dispatcher.add_handler(CommandHandler('_debts', self._debts))
        updater.dispatcher.add_handler(CommandHandler('_bot_off', self._bot_off))
        updater.dispatcher.add_handler(CommandHandler('_bot_on', self._bot_on))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))
        updater.dispatcher.add_handler(CommandHandler('help', self.help_command))
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))
        dispatcher.add_error_handler(self.error)

        updater.start_polling()
        updater.idle()
