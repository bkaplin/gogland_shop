# -*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _, gettext_lazy as l_
from django.db.models import SET_NULL, Q

from coupon.models import Coupon
from user.models import User


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name=l_(u'Название категории'), null=True, blank=True)
    parent = models.ForeignKey('self', verbose_name=l_(u'Родительская категория'),
                               related_name='child_categories',
                               on_delete=SET_NULL, null=True, blank=True)
    position = models.PositiveSmallIntegerField(verbose_name=l_(u'номер по порядку'),
                                                help_text=l_(u'чем меньше, тем выше находится'), default=1)

    class Meta:
        verbose_name = l_(u'Категория')
        verbose_name_plural = l_(u'Категории')
        ordering = ['name']

    def __str__(self):
        return self.name or str(self.pk)

    def has_products(self, user_tg_id=None):
        VIP_USERS_TG_IDS = set(list(User.objects.filter(is_vip=True).values_list('tg_id', flat=True)))

        child_categories = self.child_categories.all()

        if self.products.exists() or not child_categories.exists():
            res_has_products = self.products.filter(rest__gt=0, is_active=True).exists()
            if user_tg_id and str(user_tg_id) in VIP_USERS_TG_IDS:
                res_has_products = self.products.filter(rest__gt=0).exists()
            return res_has_products

        for category in child_categories:
            if category.has_products(user_tg_id):
                return True
        return False

    def get_self_with_parents(self):
        res = [self]
        if self.parent:
            res += self.parent.get_self_with_parents()
        return res


class AdditionalProperty(models.Model):
    name = models.CharField(max_length=255, verbose_name=l_(u'Название свойства'), null=True, blank=True)
    warning_message = models.TextField(verbose_name=l_(u'Текст предупреждения'), null=True, blank=True)

    class Meta:
        verbose_name = l_(u'Дополнительное свойство товара')
        verbose_name_plural = l_(u'Дополнительные свойства товара')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name=l_(u'Название продукта'), null=True, blank=True)
    category = models.ForeignKey(Category, verbose_name=l_(u'Категория'), related_name='products', on_delete=SET_NULL, null=True)
    rest = models.IntegerField(verbose_name=l_(u'Остаток'), default=0)
    sb_price = models.FloatField(verbose_name=l_(u'Цена закупки'), default=0)
    price = models.FloatField(verbose_name=l_(u'Цена'), default=0)
    is_active = models.BooleanField(verbose_name=l_(u'Активен для продажи'), default=True)

    hidden_for_all = models.BooleanField(verbose_name=l_(u'Скрыт для всех (админов в тч)'),
                                         help_text=l_(u'Например, когда товар пока не в продаже, '
                                                      u'а планируется только в будущем, поставить галку до тех пор, '
                                                      u'пока не будет решено начать продавать'),
                                         default=False)
    additional_property = models.ForeignKey(AdditionalProperty,
                                            verbose_name=l_(u'Дополнительное свойство'),
                                            on_delete=SET_NULL,
                                            blank=True, null=True)

    class Meta:
        verbose_name = l_(u'Продукт')
        verbose_name_plural = l_(u'Продукты')
        ordering = ['name']

    def __str__(self):
        return self.name or str(self.pk)

    @property
    def _menu_label(self):
        return settings.FIRE_ICON if not self.is_active or self.hidden_for_all else ''

    @property
    def price_int(self):
        return int(self.price)

    def get_active_coupons(self):
        today = datetime.today()
        return Coupon.objects.filter(
            Q(active=True, start_at__lte=today, end_at__gte=today) &
            Q(
                Q(products__exact=self) | Q(categories__in=self.category.get_self_with_parents())
            )
        )

    def price_with_coupon(self):
        coupon = self.get_active_coupons().first()
        if coupon:
            new_price = self.price * (1 - float(
                coupon.coupon_percent) / 100) if coupon.coupon_percent else self.price - coupon.coupon_fixed
            return int(new_price)
        return self.price_int
