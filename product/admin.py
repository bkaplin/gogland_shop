from django.contrib import admin
from product.models import Product, Category


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
        'is_active',
    ]
    search_fields = [
        'id',
        'name',
        'category',
    ]


admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
