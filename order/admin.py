from django.contrib import admin
from order.models import Order, OrderItem


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