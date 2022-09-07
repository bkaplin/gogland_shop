from django.contrib import admin
from user.models import User
from django.utils.translation import gettext as _, gettext_lazy as l_


class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'last_name',
        'first_name',
        'tg_id',
        'is_active',
        'is_verified'
    ]
    list_filter = [
        'is_active',
        'is_verified'
    ]

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_active.short_description = _(u'Сделать активными')

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = _(u'Сделать НЕактивными')

    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)
    mark_verified.short_description = _(u'Сделать верифицированными')

    def mark_inverified(self, request, queryset):
        queryset.update(is_verified=False)
    mark_inverified.short_description = _(u'Сделать НЕ верифицированными')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "password":
            kwargs["required"] = False
        return super(UserAdmin, self).formfield_for_dbfield(db_field, request, **kwargs)

    actions = [
        'mark_active',
        'mark_inactive',
        'mark_verified',
        'mark_inverified',
    ]


admin.site.register(User, UserAdmin)
