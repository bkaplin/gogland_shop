from django.contrib import admin
from django.db.models import Sum

from order.models import Order, OrderItem
from django.utils.translation import gettext as _, gettext_lazy as l_
from django.contrib.admin.views.main import ChangeList


class OrderChangeList(ChangeList):

    def get_results(self, *args, **kwargs):
        super(OrderChangeList, self).get_results(*args, **kwargs)
        q = self.result_list.aggregate(total_sum=Sum('total'), total_profit=Sum('profit'))
        self.total_sum = q['total_sum']
        self.total_profit = q['total_profit']
        q_all = self.model.objects.filter(is_payed=True, is_closed=True).aggregate(total_sum=Sum('total'),
                                                                                   total_profit=Sum('profit'))
        self.TOTAL_SUM = q_all['total_sum']
        self.TOTAL_PROFIT = q_all['total_profit']


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'created',
        'in_cart',
        'is_payed',
        'is_closed',
        'cancelled',
        'total',
        'profit_fmt',
        'comment',
    ]
    list_filter = [
        'user',
        'created',
        'in_cart',
        'is_payed',
        'is_closed',
        'cancelled'
    ]
    search_fields = [
        'id',
        'user__last_name',
        'user__tg_id',
    ]

    def profit_fmt(self, obj):
        return round(obj.profit, 2)
    profit_fmt.short_description = l_(u'Прибыль')
    profit_fmt.admin_order_field = 'profit'

    def get_changelist(self, request):
        return OrderChangeList

    class OrderItemInline(admin.TabularInline):
        model = OrderItem
        extra = 0
        allow_add = True

        raw_id_fields = ('product',)

        autocomplete_lookup_fields = {
            'fk': ['product', ],
        }

    inlines = (OrderItemInline, )

    def mark_payed(self, request, queryset):
        queryset.update(is_payed=True, is_closed=True)
    mark_payed.short_description = _(u'Оплачено')

    def mark_closed(self, request, queryset):
        queryset.update(is_closed=True)
    mark_closed.short_description = _(u'Закрыть')

    def mark_cancelled(self, request, queryset):
        for order in queryset:
            order.cancel_order_n_recalculate_rests()
    mark_cancelled.short_description = _(u'Отменить')

    def mark_unpayed(self, request, queryset):
        queryset.update(is_payed=False, is_closed=False)
    mark_unpayed.short_description = _(u'НЕ Оплачено')

    def mark_unclosed(self, request, queryset):
        queryset.update(is_closed=False)
    mark_unclosed.short_description = _(u'Открыть заново')

    def mark_uncancelled(self, request, queryset):
        queryset.update(cancelled=False, is_closed=False)
    mark_uncancelled.short_description = _(u'НЕ Отменять')

    actions = [
        'mark_payed',
        'mark_closed',
        'mark_cancelled',
        'mark_unpayed',
        'mark_unclosed',
        'mark_uncancelled',
    ]


class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'product',
        'count',
        'sync',
        'in_process',
        'sum',
        'order_created'
    ]
    list_filter = [
        'product',
        'sync',
        'in_process',
    ]
    search_fields = [
        'id',
        'order__id',
        'product__name',
        'product__id'
    ]

    def order_created(self, obj):
        return obj.order.created
    order_created.short_description = l_(u'Дата заказа')
    order_created.admin_order_field = 'order__created'


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)