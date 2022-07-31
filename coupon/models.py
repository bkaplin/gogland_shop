# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import gettext as _, gettext_lazy as l_


class Coupon(models.Model):
    name = models.CharField(verbose_name=l_('Название'), max_length=255, blank=True, null=True)
    active = models.BooleanField(verbose_name=l_('Активна'), default=False)
    start_at = models.DateField(verbose_name=l_('Действует С'), blank=True, null=True)
    end_at = models.DateField(verbose_name=l_('Действует ДО'), blank=True, null=True)
    products = models.ManyToManyField('product.Product', verbose_name=l_('Продукты'), related_name='coupons', blank=True)
    categories = models.ManyToManyField('product.Category', verbose_name=l_('Категории'), related_name='coupons', blank=True)
    coupon_percent = models.PositiveSmallIntegerField(default=0,
                                                      verbose_name=l_(u'Величина Скидки, %'),
                                                      null=True, blank=True)
    coupon_fixed = models.PositiveIntegerField(default=0,
                                               null=True, blank=True, verbose_name=l_(u'Величина Скидки, фикс.'))

    class Meta:
        verbose_name = l_('Скидка')
        verbose_name_plural = l_('Скидки')

    def __str__(self):
        coupon_value = f'{self.coupon_percent}%' if self.coupon_percent else f'{self.coupon_fixed}₽'
        return f'{self.name or "Без имени"}: {coupon_value}'
