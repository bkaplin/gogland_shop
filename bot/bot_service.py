import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from django.conf import settings

from bot.models import Chat, CardNumber, ShopSettings, Message
from order.models import Order, OrderItem
from product.models import Category, Product
from user.models import User

# Ведение журнала логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotService:

    def __init__(self):
        self.bot = telegram.Bot(token=settings.TG_TOKEN)
        self.cart_number = CardNumber.objects.filter(is_active=True).first()
        self.cart_info_message = f"Оплатить по номеру карты \n\n `{self.cart_number.number}`\n (нажать, чтобы скопировать)." if self.cart_number else ""

    @staticmethod
    def dotval(obj, attr, default=None):
        return getattr(obj, attr) if hasattr(obj, attr) else default

    def _init_admins_chat(self, update, _):
        """Вызывается по команде `/_init_admins_chat`."""
        user = update.message.from_user
        user_id = self.dotval(user, 'id')
        if settings.CORRECT_USERS and str(user_id) not in settings.CORRECT_USERS:
            raise Exception

        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user or not local_user.is_admin:
            raise Exception

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
        user = update.message.from_user
        user_id = self.dotval(user, 'id')
        if settings.CORRECT_USERS and str(user_id) not in settings.CORRECT_USERS:
            raise Exception

        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user or not local_user.is_admin:
            raise Exception

        chat_id = update.message.chat_id

        admins_chat = Chat.objects.filter(tg_id=chat_id, is_admins_chat=True).first()
        if admins_chat:
            admins_chat.is_admins_chat = False
            admins_chat.save(update_fields=['is_admins_chat'])
            logger.info(f"Чат админов удалён: {chat_id}")
            self.bot.send_message(chat_id=admins_chat.tg_id, text="Чат админов удалён. "
                                                                  "Теперь тут НЕ будут присылаться оповещания о заказах")
        return

    def start(self, update, _):
        """Вызывается по команде `/start`."""
        # Получаем пользователя, который запустил команду `/start`
        user = update.message.from_user
        user_id = self.dotval(user, 'id')
        if settings.CORRECT_USERS and str(user_id) not in settings.CORRECT_USERS:
            raise Exception

        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user:
            local_user, created = User.objects.get_or_create(
                tg_id=user_id,
                last_name=self.dotval(user, 'last_name', ''),
                first_name=self.dotval(user, 'first_name'),
                username=self.dotval(user, 'username', '')
            )
        local_chat = Chat.objects.filter(tg_id=user_id).first()
        if not local_chat:
            Chat.objects.create(
                user=local_user,
                tg_id=user_id
            )
        logger.info(f"Пользователь {user_id}:{user.first_name} зашел")

        orders_in_cart = local_user.orders.filter(in_cart=True)
        for order in orders_in_cart:
            order.cancel_order_n_recalculate_rests()

        # # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
        self.send_root_menu(update, False)

    def send_root_menu(self, update, user_has_order_in_cart, additional_message=''):
        keyboard = self.get_root_menu(user_has_order_in_cart)
        reply_markup = InlineKeyboardMarkup(keyboard)

        work_time = ShopSettings.objects.first().work_time
        work_time_text = f'*** Время работы магазина {work_time} ***'
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
                InlineKeyboardButton(f"Оплачено {settings.PAYED_ICON}", callback_data=str(f'__payed-{order_id}')))
        if cancel_btn:
            bottom_buttons.append(
                InlineKeyboardButton(f"Отменить {settings.CANCELLED_ICON}", callback_data=str(f'__cancel-{order_id}')))
        l.append(bottom_buttons)

        return l

    def get_cancel_order_button(self, order_id):
        bottom_buttons = []
        bottom_buttons.append(InlineKeyboardButton(f"Отменить {settings.CANCELLED_ICON}", callback_data=str(f'__cancel-{order_id}')))
        return [bottom_buttons]

    def get_root_menu(self, user_has_order_in_cart, user_tg_id=None):
        l = [[InlineKeyboardButton(c.name, callback_data=str(c.pk))] for c in Category.objects.filter(parent__isnull=True).order_by('position') if c.has_products(user_tg_id)]

        bottom_buttons = []
        if user_has_order_in_cart:
            bottom_buttons.append(InlineKeyboardButton("Оформить", callback_data=str('confirm')))
        bottom_buttons.append(InlineKeyboardButton("Отмена", callback_data=str('exit')))
        l.append(bottom_buttons)
        return l

    def get_buttons(self, category, user_has_order_in_cart, user_tg_id=None):
        if not category:
            return
        childs_categories = category.child_categories.order_by('position')
        category_products = category.products.filter(rest__gt=0, is_active=True)
        VIP_USERS_TG_IDS = set(list(User.objects.filter(is_vip=True).values_list('tg_id', flat=True)))

        if user_tg_id and str(user_tg_id) in VIP_USERS_TG_IDS:
            category_products = category.products.filter(rest__gt=0)

        bottom_buttons = []
        if childs_categories.exists():
            l = [[InlineKeyboardButton(c.name, callback_data=str(c.pk))] for c in childs_categories if c.has_products(user_tg_id)]
        else:
            l = [[InlineKeyboardButton(f'{p.name} {p.price_int} ₽ (Ост. {p.rest if p.rest <= 10 else ">10"})', callback_data=f'buy{p.pk}')] for p in category_products]

        if user_has_order_in_cart:
            bottom_buttons.append(InlineKeyboardButton("Оформить", callback_data=str('confirm')))
        bottom_buttons += [
            InlineKeyboardButton("Отмена", callback_data=str('exit')),
            InlineKeyboardButton("Назад", callback_data='back_to' + str(category.parent.pk if category.parent else '')),
        ]
        l.append(bottom_buttons)

        return l

    def button(self, update, _):
        query = update.callback_query
        variant = query.data

        user = query.from_user
        user_id = self.dotval(user, 'id')
        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user:
            local_user, created = User.objects.get_or_create(
                tg_id=user_id,
                last_name=self.dotval(user, 'last_name'),
                first_name=self.dotval(user, 'first_name'),
                username=self.dotval(user, 'username')
            )

        local_chat = Chat.objects.filter(tg_id=user_id).first()
        if not local_chat:
            Chat.objects.create(
                user=local_user,
                tg_id=user_id
            )

        # если идет работа над заказом со стороны админа (оплачено/отменено)
        if variant.startswith('__'):
            order_id = variant.split('-')[-1]

            # берем текст сообщения минус последний символ, в котором значок ⚠
            answer_text = query.message.text[:-1]
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
                            if not _order.is_payed:
                                _order.set_payed()
                            answer_text += settings.PAYED_ICON
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

        work_time = ShopSettings.objects.first().work_time
        work_time_text = f'*** Время работы магазина {work_time} ***'

        buy = False
        order = local_user.orders.filter(in_cart=True).first()
        additional_message = order.info if order else ''

        if variant.startswith('back_to'):
            variant = variant.replace('back_to', '')
        elif variant == 'exit':
            if order:
                order.cancel_order_n_recalculate_rests()
                logger.info(f"Пользователь {user_id}:{user.first_name} отменил заказ №{order.pk}")

            query.edit_message_text(text="Приходите еще")

            logger.info(f"Пользователь {user_id}:{user.first_name} вышел")
            return ConversationHandler.END
        elif variant == 'confirm' and order:
            order.in_cart = False
            order.update_sum()
            order.recalculate_rests()

            logger.info(f"Пользователь {user_id}:{user.first_name} оформил заказ №{order.pk} на {order.total_int} ₽")

            # отправка сообщений в чаты админов о новом заказе
            order_buttons_for_admin = self.get_order_buttons(order.id)
            order_reply_markup_for_admin = InlineKeyboardMarkup(order_buttons_for_admin)

            admins_chats = Chat.objects.filter(is_admins_chat=True)
            message_to_admins = f"Сделан заказ №{order.pk} на {order.total_int} ₽ от {order.user}\n\n{order.info}{settings.WARNING_ICON}"
            for admin_chat in admins_chats:
                tg_message = self.bot.send_message(
                    text=message_to_admins,
                    chat_id=admin_chat.tg_id,
                    reply_markup=order_reply_markup_for_admin
                )
                Message.objects.create(
                    chat=admin_chat,
                    text=message_to_admins,
                    message_id=tg_message.message_id,
                    order_id=order.pk,
                    is_for_admins=True,
                )

            # отправляем сообщение покупателю и создаем сообщение
            order_buttons_for_user = self.get_cancel_order_button(order.id)
            order_reply_markup_for_user = InlineKeyboardMarkup(order_buttons_for_user)
            message_to_user = f"Заказ оформлен.\n{order.info}{self.cart_info_message}"
            query.edit_message_text(
                text=message_to_user,
                parse_mode=telegram.ParseMode.MARKDOWN,
                reply_markup=order_reply_markup_for_user
            )
            Message.objects.create(
                chat=local_chat,
                text=message_to_user,
                message_id=query.message.message_id,
                order_id=order.pk,
            )
            return

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

        category = None
        user_has_order_in_cart = local_user.orders.filter(in_cart=True, items__isnull=False).exclude(items__count__lt=1).exists()
        if variant:
            category = Category.objects.filter(pk=variant).first()
            buttons = self.get_buttons(category, user_has_order_in_cart, user_tg_id=user_id)
        else:
            buttons = self.get_root_menu(user_has_order_in_cart)
        reply_markup = InlineKeyboardMarkup(buttons)

        # `CallbackQueries` требует ответа, даже если
        # уведомление для пользователя не требуется, в противном
        #  случае у некоторых клиентов могут возникнуть проблемы.
        # смотри https://core.telegram.org/bots/api#callbackquery.
        query.answer()
        # редактируем сообщение, тем самым кнопки
        # в чате заменятся на этот ответ.
        query.edit_message_text(text=f"{work_time_text}\n{additional_message}{category.name if category else 'Выберете товар'}", reply_markup=reply_markup)

    @staticmethod
    def help_command(update, _):
        update.message.reply_text("Используйте `/start` для тестирования.")

    @staticmethod
    def error(update, context):
        update.message.reply_text('Что-то пошло не так. Отправьте корректный выбор.')

    def text(self, update, context):
        text_received = update.message.text
        user = update.message.from_user
        user_id = self.dotval(user, 'id')
        local_user = User.objects.filter(tg_id=user_id).first()
        if not local_user:
            return
        order = local_user.orders.filter(in_cart=True).first()
        oi = order.items.filter(in_process=True).first()

        if not oi:
            return
        count = float(text_received)
        if count == 0:
            oi.delete()
            additional_message = f'{order.info}'
            self.send_root_menu(update, user_has_order_in_cart=True and order.items.exists(), additional_message=additional_message)
            return
        if count < 0:
            raise Exception
        valid_count = count if count <= oi.product.rest else oi.product.rest
        oi.count += valid_count
        oi.in_process = False
        oi.save()

        logger.info(f"Пользователь {user_id}:{user.first_name} добавил продукт {oi.product.pk}:{oi.product.name} в количестве {valid_count} шт. на сумму {oi.product.price * valid_count} ₽")

        max_count = count >= oi.product.rest
        oi.reduce_rest(valid_count)
        order.update_sum()

        max_count_message = "(Максимальное количество)" if max_count else ""
        additional_message = f'Добавлен товар {oi.product.name} в количестве {int(oi.count)}шт.{max_count_message} на {oi.sum_int} ₽\n\n{order.info}'

        self.send_root_menu(update, user_has_order_in_cart=True and order.items.exists(), additional_message=additional_message)

        # update.message.reply_text('an error occured')

    def main(self):
        updater = Updater(settings.TG_TOKEN)
        dispatcher = updater.dispatcher

        updater.dispatcher.add_handler(CommandHandler('start', self.start))
        updater.dispatcher.add_handler(CommandHandler('_init_admins_chat', self._init_admins_chat))
        updater.dispatcher.add_handler(CommandHandler('_delete_admins_chat', self._delete_admins_chat))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))
        updater.dispatcher.add_handler(CommandHandler('help', self.help_command))
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))
        dispatcher.add_error_handler(self.error)

        updater.start_polling()
        updater.idle()
