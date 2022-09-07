# -*- coding: utf-8 -*-

from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import SET_NULL
from django.utils.translation import gettext as _, gettext_lazy as l_
from django.db import models
from django.core.validators import RegexValidator

PHONE_VALIDATOR = RegexValidator(regex=r'[0-9( )\-+]{6,20}',
                                 message=l_(u'Телефон должен состоять из цифр +-(). Введите корректный номер телефона.'))


class User(AbstractBaseUser):
    USERNAME_FIELD = 'tg_id'

    created = models.DateTimeField(verbose_name=l_(u'Дата создания'), auto_now_add=True, blank=True, null=True)

    username = models.CharField(l_('username'), max_length=255, blank=True, null=True)
    phone = models.CharField(
        l_(u'Контактный телефон'), max_length=30, validators=[PHONE_VALIDATOR], default='',
        blank=True
    )
    first_name = models.CharField(l_('имя'), default='', max_length=255, blank=True)
    last_name = models.CharField(l_('фамилия'), default='', max_length=255, blank=True, null=True)
    tg_id = models.CharField(max_length=255, verbose_name=l_(u'ID пользователя в TG'), blank=True, null=True)
    is_active = models.BooleanField(verbose_name=l_('Активный'), default=True)

    is_admin = models.BooleanField(verbose_name=l_('Админ'), default=False)
    is_vip = models.BooleanField(verbose_name=l_('VIP'), default=False)
    is_verified = models.BooleanField(verbose_name=l_('Верифицирован'), default=False)

    class Meta:
        verbose_name = l_(u'Пользователь')
        verbose_name_plural = l_(u'Пользователи')

    def __str__(self):
        return self.full_name or str(self.pk)

    @property
    def full_name(self):
        return f'{self.last_name or ""} {self.first_name}'
