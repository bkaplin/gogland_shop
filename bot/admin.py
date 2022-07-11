from django.contrib import admin

from bot.models import Chat, CardNumber, ShopSettings, GroupBotMessage
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
            kwargs["queryset"] = User.objects.filter(is_active=True)
        return super(GroupBotMessageAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    actions = [
        'send',
    ]


admin.site.register(Chat)
admin.site.register(CardNumber)
admin.site.register(ShopSettings)
admin.site.register(GroupBotMessage, GroupBotMessageAdmin)

