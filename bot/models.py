import datetime
import time

from django.conf import settings
from django.db import models
from django.db.models import SET_NULL
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy as l_
from solo.models import SingletonModel

from order.models import Order
from user.models import User
import telegram


class Chat(models.Model):
    user = models.ForeignKey(User, verbose_name=l_(u'Пользователь'), related_name='chats', null=True, blank=True, on_delete=SET_NULL)
    tg_id = models.CharField(max_length=255, verbose_name=l_(u'ID чата в TG'))

    is_admins_chat = models.BooleanField(verbose_name=l_('Чат админов'), default=False)

    class Meta:
        verbose_name = l_(u'Чат')
        verbose_name_plural = l_(u'Чаты')

    def __str__(self):
        return self.user.full_name if self.user else None or str(self.pk)


class Message(models.Model):
    chat = models.ForeignKey(Chat, verbose_name=l_(u'Чат'), related_name='messages', null=True, blank=True, on_delete=SET_NULL)
    order = models.ForeignKey(Order, verbose_name=l_(u'Заказ'), related_name='messages', null=True, blank=True, on_delete=SET_NULL)
    text = models.CharField(max_length=255, verbose_name=l_(u'Текс сообщения'), blank=True, null=True)
    created = models.DateTimeField(verbose_name=l_(u'Дата создания'), auto_now_add=True)
    message_id = models.CharField(max_length=10, verbose_name=l_('ID сообщения в TG'), blank=True, null=True)
    is_for_admins = models.BooleanField(verbose_name=l_('Для админов'), default=False)

    class Meta:
        verbose_name = l_(u'Сообщение')
        verbose_name_plural = l_(u'Сообщения')

    def __str__(self):
        return f'{self.chat.user}: {self.text}' if self.chat and self.chat.user else f'{self.pk}: {self.text}'


class GroupBotMessage(models.Model):
    created_at = models.DateTimeField(verbose_name=l_(u'Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=l_(u'Дата обновления'), auto_now_add=True)
    sent_at = models.DateTimeField(verbose_name=l_(u'Дата последней отправки'), blank=True, null=True)

    users = models.ManyToManyField(User, verbose_name=l_(u'Пользователи для отправки сообщения'), related_name='group_messages')
    message_text = models.TextField(verbose_name=l_(u'Текст сообщения'), default='')
    sent = models.BooleanField(verbose_name=l_(u'Отправлено'), default=False)
    log = models.TextField(verbose_name=l_(u'Лог отправки'), default='', blank=True, null=True)

    class Meta:
        verbose_name = l_(u'Групповое сообщение от бота')
        verbose_name_plural = l_(u'Групповые сообщения от бота')

    def __str__(self):
        return self.message_text

    def send(self):
        bot = telegram.Bot(token=settings.TG_TOKEN)
        now = timezone.now()
        self.sent_at = now
        self.sent = True

        log_item = '{}: {}\t{}\n'

        self.log += f'{now.strftime("%d.%m.%Y %H:%M:%S")}\n'

        for user in self.users.all():
            time.sleep(1)
            try:
                bot.send_message(text=self.message_text, chat_id=user.tg_id)
                status = 'OK'
            except:
                status = 'ERROR'
            self.log += log_item.format(user.tg_id, user.full_name, status)
        self.log += '\n\n'

        self.save()


class CardNumber(models.Model):
    number = models.CharField(max_length=255, verbose_name=l_(u'Номер карты'))
    owner = models.CharField(max_length=255, verbose_name=l_(u'Владелец'))
    is_active = models.BooleanField(verbose_name=l_(u'Активна'), default=False)

    class Meta:
        verbose_name = l_(u'Номер карты (админ)')
        verbose_name_plural = l_(u'Номера карт (админ)')

    def __str__(self):
        return f'{self.number} {self.owner}'


class ShopSettings(SingletonModel):
    work_time = models.CharField(verbose_name=l_(u'Время работы магазина сегодня'), max_length=255, default=u'11 - 19',
                                 editable=False)
    work_start = models.TimeField(verbose_name=l_(u'Время начала работы магазина сегодня'), blank=True, null=True)
    work_end = models.TimeField(verbose_name=l_(u'Время окончания работы магазина сегодня'), blank=True, null=True)
    enable_verification = models.BooleanField(verbose_name=l_(u'Включить верификацию пользователей'), default=False)

    disable_bot = models.BooleanField(verbose_name=l_(u'Выключить бота'), default=False,
                                      help_text=l_(u'Полностью выключить бота (не будет возможности делать заказы)'))

    class Meta:
        verbose_name = l_(u'Настройки магазина')
        verbose_name_plural = verbose_name

    @property
    def work_time_today(self):
        return f'{self.work_start.strftime("%H:%M")} - {self.work_end.strftime("%H:%M")}'

    def __str__(self):
        return str(self._meta.verbose_name)
