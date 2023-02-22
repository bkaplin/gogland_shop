from django.contrib import admin
from product.models import Product, Category, AdditionalProperty


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'category',
        'rest',
        'sb_price',
        'price',
        'is_active',
    ]
    list_filter = [
        'category',
        'is_active'
    ]
    search_fields = [
        'name',
        'category__name'
    ]


class AdditionalPropertyAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'warning_message',
    ]


admin.site.register(Product, ProductAdmin)
admin.site.register(AdditionalProperty, AdditionalPropertyAdmin)
admin.site.register(Category)
