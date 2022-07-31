from django.contrib import admin
from django import forms

from coupon.models import Coupon


class CouponAdmin(admin.ModelAdmin):
    pass


admin.site.register(Coupon, CouponAdmin)
