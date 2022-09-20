from django.contrib import admin
from solo.admin import SingletonModelAdmin

from bot.models import Chat, CardNumber, ShopSettings, GroupBotMessage, Message
from django.utils.translation import gettext as _, gettext_lazy as l_

from user.models import User


class GroupBotMessageAdmin(admin.ModelAdmin):
    EMPTY_LABEL = '-'

    list_display = [
        'id',
        'message_text',
        'sent',

        'created_at',
        'updated_at',
        'sent_at',
    ]

    list_display_links = [
        'id',
        'message_text',
    ]

    readonly_fields = [
        'log',
        'created_at',
        'updated_at',
        'sent_at',
        'sent',
    ]

    search_fields = [
        'message_text',
    ]

    list_filter = [
        'sent',
    ]

    def send(self, request, queryset):
        for item in queryset:
            item.send()
    send.short_description = _(u'Отправить')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "users":
            kwargs["queryset"] = User.objects.filter(is_active=True, is_verified=True)
        return super(GroupBotMessageAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    actions = [
        'send',
    ]


class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'chat',
        'order',
        'text',
        'created',
        'message_id',
        'is_for_admins',
    ]

    readonly_fields = [
        'chat',
        'order',
        'text',
        'created',
        'message_id',
        'is_for_admins',
    ]

    search_fields = [
        'order_id',
        'chat__user__last_name',
        'chat__user__first_name',
    ]

    list_filter = [
        'created',
        'is_for_admins',
        'chat',
    ]


class ShopSettingsAdmin(SingletonModelAdmin):
    fieldsets = [
        (
            _('Настройки работы магазина'),
            {'fields': (
                'work_start',
                'work_end',
            )}
        ),
        (
            _('Настройки верификации'),
            {'fields': (
                'enable_verification',
            )}
        ),
    ]


admin.site.register(Chat)
admin.site.register(Message, MessageAdmin)
admin.site.register(CardNumber)
admin.site.register(ShopSettings, ShopSettingsAdmin)
admin.site.register(GroupBotMessage, GroupBotMessageAdmin)

