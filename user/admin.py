from django.contrib import admin
from user.models import User


class UserAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "password":
            kwargs["required"] = False
        return super(UserAdmin, self).formfield_for_dbfield(db_field, request, **kwargs)


admin.site.register(User, UserAdmin)
