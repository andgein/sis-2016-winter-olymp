from django.contrib import admin

from . import models


class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'open_locality', 'ejudge_user_id')

admin.site.register(models.UserInfo, UserInfoAdmin)
