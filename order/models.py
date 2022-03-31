# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import gettext as _, gettext_lazy as l_
from django.db.models import SET_NULL

from product.models import Product
from user.models import User


class Order(models.Model):
    in_cart = models.BooleanField(verbose_name=l_(u'В корзине'), default=True)
    created = models.DateTimeField(verbose_name=l_(u'Дата создания'), auto_now_add=True, blank=True, null=True)
    user = models.ForeignKey(User, verbose_name=l_(u'Пользователь'), related_name='orders', on_delete=SET_NULL, null=True)
    total = models.FloatField(verbose_name=l_(u'Итого'), default=0)
    is_payed = models.BooleanField(verbose_name=l_(u'Оплачен'), default=False)
    is_closed = models.BooleanField(verbose_name=l_(u'Закрыт'), default=False)
    profit = models.FloatField(verbose_name=l_(u'Прибыль'), default=0)

    class Meta:
        verbose_name = l_(u'Заказ')
        verbose_name_plural = l_(u'Заказы')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=l_(u'Позиция'), related_name='items', on_delete=SET_NULL, null=True)
    product = models.ForeignKey(Product, verbose_name=l_(u'Продукт'), on_delete=SET_NULL, null=True)
    count = models.IntegerField(verbose_name=l_('Количество'), default=1)

    class Meta:
        verbose_name = l_(u'Позиция')
        verbose_name_plural = l_(u'Позиции')