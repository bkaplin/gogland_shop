from django.contrib import admin
from order.models import Order, OrderItem
from django.utils.translation import gettext as _, gettext_lazy as l_


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
        'profit'
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
        queryset.update(cancelled=True, is_closed=True)
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
    ]
    list_filter = [
        'order',
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


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)