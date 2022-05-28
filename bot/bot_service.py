import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from django.conf import settings

from bot.models import Chat, CardNumber, ShopSettings
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
        self.cart_info_message = f"Оплатить по номеру карты \n\n `{self.cart_number.number}`\n (нажать, чтобы скопировать)" if self.cart_number else ""

    @staticmethod
    def dotval(obj, attr, default=None):
        return getattr(obj, attr) if hasattr(obj, attr) else default

    def start(self, update, _):
        """Вызывается по команде `/start`."""
        # Получаем пользователя, который запустил команду `/start`
        user = update.message.from_user
        user_id = self.dotval(user, 'id')
        if not user_id:
            print("NNOOOOOTTTT IIIIDDDD!!!!")
        logger.info(f"!!! user_id {user_id}:{user.first_name} жмакнул старт")
        local_user = User.objects.filter(tg_id=user_id).first()
        logger.info(f"RTRTTRTRTRTRTRTRTRTRTRTRTRTRT {local_user}, {self.dotval(user, 'username')}")
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

    def get_root_menu(self, user_has_order_in_cart):
        l = [[InlineKeyboardButton(c.name, callback_data=str(c.pk))] for c in Category.objects.filter(parent__isnull=True).order_by('position') if c.has_products]

        bottom_buttons = []
        if user_has_order_in_cart:
            bottom_buttons.append(InlineKeyboardButton("Оформить", callback_data=str('confirm')))
        bottom_buttons.append(InlineKeyboardButton("Отмена", callback_data=str('exit')))
        l.append(bottom_buttons)
        return l

    def get_buttons(self, category, user_has_order_in_cart):
        if not category:
            return
        childs_categories = category.child_categories.order_by('position')
        bottom_buttons = []
        if childs_categories.exists():
            l = [[InlineKeyboardButton(c.name, callback_data=str(c.pk))] for c in childs_categories if c.has_products]
        else:
            l = [[InlineKeyboardButton(f'{p.name} {p.price_int} ₽ (Ост. {p.rest if p.rest <= 10 else ">10"})', callback_data=f'buy{p.pk}')] for p in category.products.filter(rest__gt=0)]

        if user_has_order_in_cart:
            bottom_buttons.append(InlineKeyboardButton("Оформить", callback_data=str('confirm')))
        bottom_buttons += [
            InlineKeyboardButton("Отмена", callback_data=str('exit')),
            InlineKeyboardButton("Назад", callback_data='back_to' + str(category.parent.pk if category.parent else '')),
        ]
        l.append(bottom_buttons)

        return l

    def button(self, update, _):
        work_time = ShopSettings.objects.first().work_time
        work_time_text = f'*** Время работы магазина {work_time} ***'

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
            query.edit_message_text(
                text=f"Заказ №{order.pk} на {order.total_int} ₽ оформлен. {self.cart_info_message}",
                parse_mode=telegram.ParseMode.MARKDOWN)

            logger.info(f"Пользователь {user_id}:{user.first_name} оформил заказ №{order.pk} на {order.total_int} ₽")

            for tg_id in settings.ADMIN_TG_IDS:
                self.bot.send_message(
                    text=f"Сделан заказ №{order.pk} на {order.total_int} ₽ от {order.user}\n\n{order.info}",
                    chat_id=tg_id)

            return
        elif variant.startswith('buy'):
            variant = variant.replace('buy', '')
            buy = True

        if buy:
            product = Product.objects.filter(pk=variant).first()
            if product:
                query.edit_message_text(text=f'Сколько нужно "{product.name}"? Отправьте количество.')
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
        user_has_order_in_cart = local_user.orders.filter(in_cart=True).exclude(items__count__lt=1).exists()
        if variant:
            category = Category.objects.filter(pk=variant).first()
            buttons = self.get_buttons(category, user_has_order_in_cart)
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
        if count <= 0:
            raise Exception
        valid_count = count if count <= oi.product.rest else oi.product.rest
        oi.count += valid_count
        oi.in_process = False
        oi.save()

        logger.info(f"Пользователь {user_id}:{user.first_name} добавил продукт {oi.product.pk}:{oi.product.name} в количестве {valid_count} шт. на сумму {oi.product.price * valid_count} ₽")

        max_count = count >= oi.product.rest
        oi.reduce_rest(valid_count)
        order.update_sum()

        max_count_message = "(Максимальное количество)" if max_count  else ""
        additional_message = f'Добавлен товар {oi.product.name} в количестве {int(oi.count)}шт.{max_count_message} на {oi.sum_int} ₽\n\n{order.info}'

        self.send_root_menu(update, True, additional_message=additional_message)

        # update.message.reply_text('an error occured')

    def main(self):
        updater = Updater(settings.TG_TOKEN)
        dispatcher = updater.dispatcher

        updater.dispatcher.add_handler(CommandHandler('start', self.start))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))
        updater.dispatcher.add_handler(CommandHandler('help', self.help_command))
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))
        dispatcher.add_error_handler(self.error)

        updater.start_polling()
        updater.idle()
