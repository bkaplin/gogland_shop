import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from django.conf import settings
from aiogram import types

from bot.models import Chat
from order.models import Order, OrderItem
from product.models import Category, Product
from user.models import User


class BotService:

    # function to handle the /start command
    @staticmethod
    def start(update, context):
        update.message.reply_text('start command received')

    # function to handle the /help command
    @staticmethod
    def help(update, context):
        update.message.reply_text('help command received')

    @staticmethod
    def menu(update, context):
        keyboard = [
            [
                InlineKeyboardButton("Option 1", callback_data='1'),
                InlineKeyboardButton("Option 2", callback_data='2'),
            ],
            [InlineKeyboardButton("Option 3", callback_data='3')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_markdown('help command received', reply_markup=reply_markup)

    # function to handle errors occured in the dispatcher
    @staticmethod
    def error(update, context):
        update.message.reply_text('an error occured')

    # function to handle normal text
    @staticmethod
    def text(update, context):
        text_received = update.message.text
        update.message.reply_text(f'did you said "{text_received}" ?')

    def main(self):
        # create the updater, that will automatically create also a dispatcher and a queue to
        # make them dialoge
        updater = Updater(settings.TG_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        # add handlers for start and help commands
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))

        dispatcher.add_handler(CommandHandler("menu", self.menu))


        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))
        # add an handler for errors
        dispatcher.add_error_handler(self.error)
        # start your shiny new bot
        updater.start_polling()
        # run the bot until Ctrl-C
        updater.idle()



# Ведение журнала логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Этапы/состояния разговора
FIRST, SECOND = range(2)
# Данные обратного вызова
ONE, TWO, THREE, FOUR = range(4)


class BotServiceV2:

    @staticmethod
    def start(update, _):
        """Вызывается по команде `/start`."""
        # Получаем пользователя, который запустил команду `/start`
        user = update.message.from_user
        logger.info("Пользователь %s начал разговор", user.first_name)
        # Создаем `InlineKeyboard`, где каждая кнопка имеет
        # отображаемый текст и строку `callback_data`
        # Клавиатура - это список строк кнопок, где каждая строка,
        # в свою очередь, является списком `[[...]]`
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data=str(ONE)),
                InlineKeyboardButton("2", callback_data=str(TWO)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
        update.message.reply_text(
            text="Запустите обработчик, выберите маршрут", reply_markup=reply_markup
        )
        # Сообщаем `ConversationHandler`, что сейчас состояние `FIRST`
        return FIRST

    @staticmethod
    def start_over(update, _):
        """Тот же текст и клавиатура, что и при `/start`, но не как новое сообщение"""
        # Получаем `CallbackQuery` из обновления `update`
        query = update.callback_query
        # На запросы обратного вызова необходимо ответить,
        # даже если уведомление для пользователя не требуется.
        # В противном случае у некоторых клиентов могут возникнуть проблемы.
        query.answer()
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data=str(ONE)),
                InlineKeyboardButton("2", callback_data=str(TWO)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Отредактируем сообщение, вызвавшее обратный вызов.
        # Это создает ощущение интерактивного меню.
        query.edit_message_text(
            text="Выберите маршрут", reply_markup=reply_markup
        )
        # Сообщаем `ConversationHandler`, что сейчас находимся в состоянии `FIRST`
        return FIRST

    @staticmethod
    def one(update, _):
        """Показ нового выбора кнопок"""
        query = update.callback_query
        query.answer()
        keyboard = [
            [
                InlineKeyboardButton("3", callback_data=str(THREE)),
                InlineKeyboardButton("4", callback_data=str(FOUR)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="Вызов `CallbackQueryHandler`, выберите маршрут", reply_markup=reply_markup
        )
        return FIRST

    @staticmethod
    def two(update, _):
        """Показ нового выбора кнопок"""
        query = update.callback_query
        query.answer()
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data=str(ONE)),
                InlineKeyboardButton("3", callback_data=str(THREE)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="Второй CallbackQueryHandler", reply_markup=reply_markup
        )
        return FIRST

    @staticmethod
    def three(update, _):
        """Показ выбора кнопок"""
        query = update.callback_query
        query.answer()
        keyboard = [
            [
                InlineKeyboardButton("Да, сделаем это снова!", callback_data=str(ONE)),
                InlineKeyboardButton("Нет, с меня хватит ...", callback_data=str(TWO)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="Третий CallbackQueryHandler. Начать сначала?", reply_markup=reply_markup
        )
        # Переход в состояние разговора `SECOND`
        return SECOND

    @staticmethod
    def four(update, _):
        """Показ выбора кнопок"""
        query = update.callback_query
        query.answer()
        keyboard = [
            [
                InlineKeyboardButton("2", callback_data=str(TWO)),
                InlineKeyboardButton("4", callback_data=str(FOUR)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="Четвертый CallbackQueryHandler, выберите маршрут", reply_markup=reply_markup
        )
        return FIRST

    @staticmethod
    def step(update, _):
        """Показ выбора кнопок"""
        query = update.callback_query
        query.answer()
        keyboard = [
            [
                InlineKeyboardButton("2", callback_data=str(TWO)),
                InlineKeyboardButton("4", callback_data=str(FOUR)),
            ],
            [
                InlineKeyboardButton("end", callback_data=str(FOUR)),
                InlineKeyboardButton("cancel", callback_data=str(FOUR)),
                InlineKeyboardButton("back", callback_data=str(FOUR)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="Четвертый CallbackQueryHandler, выберите маршрут", reply_markup=reply_markup
        )
        return FIRST

    @staticmethod
    def end(update, _):
        """Возвращает `ConversationHandler.END`, который говорит
        `ConversationHandler` что разговор окончен"""
        query = update.callback_query
        query.answer()
        query.edit_message_text(text="See you next time!")
        return ConversationHandler.END

    def main(self):
        updater = Updater(settings.TG_TOKEN)
        dispatcher = updater.dispatcher

        # Настройка обработчика разговоров с состояниями `FIRST` и `SECOND`
        # Используем параметр `pattern` для передачи `CallbackQueries` с
        # определенным шаблоном данных соответствующим обработчикам
        # ^ - означает "начало строки"
        # $ - означает "конец строки"
        # Таким образом, паттерн `^ABC$` будет ловить только 'ABC'
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={  # словарь состояний разговора, возвращаемых callback функциями
                FIRST: [
                    CallbackQueryHandler(self.one, pattern='^' + str(ONE) + '$'),
                    CallbackQueryHandler(self.two, pattern='^' + str(TWO) + '$'),
                    CallbackQueryHandler(self.three, pattern='^' + str(THREE) + '$'),
                    CallbackQueryHandler(self.four, pattern='^' + str(FOUR) + '$'),
                ],
                SECOND: [
                    CallbackQueryHandler(self.start_over, pattern='^' + str(ONE) + '$'),
                    CallbackQueryHandler(self.end, pattern='^' + str(TWO) + '$'),
                ],
            },
            fallbacks=[CommandHandler('start', self.start)],
        )

        # Добавляем `ConversationHandler` в диспетчер, который
        # будет использоваться для обработки обновлений
        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()

    # def build_menu_dict(self):
    #     d = {}
    #     depth = 0
    #     root_categories = Category.objects.filter(parent__isnull=True).order_by('position')
    #     for cat in root_categories:
    #
    #         childs = cat.childs.order_by('position')
    #
    # def temp(self, d, cat, ind):
    #     childs = cat.childs.order_by('position')
    #     if childs:
    #         if not d.get(ind):
    #             d[ind] = []
    #         d[ind].append(cat)
    #
    #         for child_cat in childs:
    #             self.temp(child_cat, ind)


class BotServiceV3(object):

    def start(self, update, _):
        """Вызывается по команде `/start`."""
        # Получаем пользователя, который запустил команду `/start`
        user = update.message.from_user
        local_user = User.objects.filter(tg_id=user.id).first()
        if not local_user:
            local_user, created = User.objects.get_or_create(
                tg_id=user.id,
                last_name=user.last_name,
                first_name=user.first_name,
                username=user.username
            )
        local_chat = Chat.objects.filter(tg_id=user.id).first()
        if not local_chat:
            Chat.objects.create(
                user=local_user,
                tg_id=user.id
            )
        logger.info("Пользователь %s начал разговор", user.first_name)

        # keyboard = self.get_root_menu()
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
        # update.message.reply_text(
        #     text="Выберете товар", reply_markup=reply_markup
        # )
        orders_in_cart = local_user.orders.filter(in_cart=True)
        for order in orders_in_cart:
            order.cancel_order_n_recalculate_rests()

        self.send_root_menu(update, False)

    def send_root_menu(self, update, user_has_order_in_cart, additional_message=''):
        keyboard = self.get_root_menu(user_has_order_in_cart)
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
        update.message.reply_text(
            text=f"{additional_message}Выберете товар", reply_markup=reply_markup
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
            l = [[InlineKeyboardButton(f'{p.name} (Ост. {p.rest if p.rest <= 10 else ">10"})', callback_data=f'buy{p.pk}')] for p in category.products.filter(rest__gt=0)]

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
        local_user = User.objects.filter(tg_id=user.id).first()
        if not local_user:
            local_user, created = User.objects.get_or_create(
                tg_id=user.id,
                last_name=user.last_name,
                first_name=user.first_name,
                username=user.username
            )

        buy = False
        order = local_user.orders.filter(in_cart=True).first()
        additional_message = order.info if order else ''

        if variant.startswith('back_to'):
            variant = variant.replace('back_to', '')
        elif variant == 'exit':
            query.edit_message_text(text="Приходите еще")
            return ConversationHandler.END
        elif variant == 'confirm' and order:
            order.in_cart = False
            order.update_sum()
            order.recalculate_rests()
            query.edit_message_text(text=f"Заказ №{order.pk} на {order.total}₽ оформлен.")
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
        query.edit_message_text(text=f"{additional_message}{category.name if category else 'Выберете товар'}", reply_markup=reply_markup)

    @staticmethod
    def help_command(update, _):
        update.message.reply_text("Используйте `/start` для тестирования.")

    @staticmethod
    def error(update, context):
        update.message.reply_text('Что-то пошло не так. Отправьте корректный выбор.')

    def text(self, update, context):
        text_received = update.message.text
        print(text_received)
        user = update.message.from_user
        local_user = User.objects.filter(tg_id=user.id).first()
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
        max_count = count >= oi.product.rest
        oi.reduce_rest(valid_count)
        order.update_sum()

        # order.combine_items()

        max_count_message = "(Максимальное количество)" if max_count  else ""
        additional_message = f'Добавлен товар {oi.product.name} в количестве {oi.count}шт.{max_count_message} на {oi.sum}₽\n\n{order.info}\n\n'

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
