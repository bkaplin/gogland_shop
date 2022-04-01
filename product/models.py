# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import gettext as _, gettext_lazy as l_
from django.db.models import SET_NULL


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

    def __str__(self):
        return self.name or str(self.pk)

    @property
    def has_products(self):
        child_categories = self.child_categories.all()

        if self.products.exists() or not child_categories.exists():
            return self.products.filter(rest__gt=0).exists()

        for category in child_categories:
            if category.has_products:
                return True
        return False


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name=l_(u'Название продукта'), null=True, blank=True)
    category = models.ForeignKey(Category, verbose_name=l_('Категория'), related_name='products', on_delete=SET_NULL, null=True)
    rest = models.IntegerField(verbose_name=l_(u'Остаток'), default=0)
    sb_price = models.FloatField(verbose_name=l_(u'Цена закупки'), default=0)
    price = models.FloatField(verbose_name=l_(u'Цена'), default=0)

    class Meta:
        verbose_name = l_(u'Продукт')
        verbose_name_plural = l_(u'Продукты')

    def __str__(self):
        return self.name or str(self.pk)
