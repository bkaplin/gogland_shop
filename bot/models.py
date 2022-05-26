from django.db import models
from django.db.models import SET_NULL
from django.utils.translation import gettext as _, gettext_lazy as l_

from user.models import User


class Chat(models.Model):
    user = models.ForeignKey(User, verbose_name=l_(u'Пользователь'), related_name='chats', null=True, blank=True, on_delete=SET_NULL)
    tg_id = models.CharField(max_length=255, verbose_name=l_(u'ID чата в TG'))

    class Meta:
        verbose_name = l_(u'Чат')
        verbose_name_plural = l_(u'Чаты')

    def __str__(self):
        return self.user.full_name or str(self.pk)


class Message(models.Model):
    chat = models.ForeignKey(Chat, verbose_name=l_(u'Чат'), related_name='messages', null=True, blank=True, on_delete=SET_NULL)
    text = models.CharField(max_length=255, verbose_name=l_(u'Текс сообщения'), blank=True, null=True)
    created = models.DateTimeField(verbose_name=l_(u'Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = l_(u'Сообщение')
        verbose_name_plural = l_(u'Сообщения')

    def __str__(self):
        return f'{self.chat.user}: {self.text}' if self.chat and self.chat.user else str(self.pk)


class CardNumber(models.Model):
    number = models.CharField(max_length=255, verbose_name=l_(u'Номер карты'))
    owner = models.CharField(max_length=255, verbose_name=l_(u'Владелец'))
    is_active = models.BooleanField(verbose_name=l_(u'Активна'), default=False)

    class Meta:
        verbose_name = l_(u'Номер карты (админ)')
        verbose_name_plural = l_(u'Номера карт (админ)')

    def __str__(self):
        return f'{self.number} {self.owner}'
