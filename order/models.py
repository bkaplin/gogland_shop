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
    cancelled = models.BooleanField(verbose_name=l_(u'Отменён'), default=False)
    profit = models.FloatField(verbose_name=l_(u'Прибыль'), default=0)

    class Meta:
        verbose_name = l_(u'Заказ')
        verbose_name_plural = l_(u'Заказы')

    def __str__(self):
        return f'{self.user.full_name if self.user else "DELETED"}: {self.pk}'

    def update_sum(self):
        total, total_profit = 0, 0
        for item in self.items.all():
            total += item.sum
            total_profit += item.count * (item.product.price - item.product.sb_price)
        self.total = total
        self.profit = total_profit
        self.save()

    def recalculate_rests(self):
        for item in self.items.filter(sync=False):
            pr = item.product
            pr.rest -= item.count
            pr.save()
            item.sync = True
            item.save()

    def cancel_order_n_recalculate_rests(self):
        for item in self.items.filter(sync=True):
            pr = item.product
            pr.rest += item.count
            pr.save()
            item.sync = False
            item.save()
        self.is_closed = True
        self.cancelled = True
        self.in_cart = False
        self.save()

    @property
    def info(self):
        items = self.items.filter(sync=True, count__gt=0)
        items_info = '\n'.join([i.info for i in items])
        return f'Заказ №{self.pk}:\n{items_info}\n\nИтого: {self.total_int} ₽\n\n'

    @property
    def total_int(self):
        return int(self.total)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=l_(u'Заказ'), related_name='items', on_delete=SET_NULL, null=True)
    product = models.ForeignKey(Product, verbose_name=l_(u'Продукт'), on_delete=SET_NULL, null=True)
    count = models.IntegerField(verbose_name=l_('Количество'), default=0)
    sync = models.BooleanField(verbose_name=l_(u'Синхронизирован'), default=False)
    in_process = models.BooleanField(verbose_name=l_(u'В процессе изменения количества'), default=False)

    class Meta:
        verbose_name = l_(u'Позиция')
        verbose_name_plural = l_(u'Позиции')

    def __str__(self):
        return f'order {self.order.pk} by {self.order.user.full_name if self.order.user else "DELETED"}: {self.product.name if self.product else self.pk} {self.count}шт.'

    @property
    def sum(self):
        return self.product.price * self.count

    @property
    def sum_int(self):
        return int(self.sum)

    @property
    def info(self):
        return f'{self.product.name}\t{self.count}шт.\t{self.sum_int} ₽'

    def reduce_rest(self, count):
        self.product.rest -= count or self.count
        self.product.save()

        self.sync = True
        self.save()

    def save(self, *args, **kwargs):
        super(OrderItem, self).save(*args, **kwargs)
        self.order.update_sum()

    def delete(self, using=None, keep_parents=False):
        o = self.order
        super(OrderItem, self).delete(using=using, keep_parents=keep_parents)
        o.update_sum()

