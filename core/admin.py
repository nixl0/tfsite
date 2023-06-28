from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from core.models import PersonalizedUser

# Register your models here.

class PerzonalizedUserInline(admin.StackedInline):
    model = PersonalizedUser
    can_delete = False
    verbose_name_plural = 'PersonalizedUsers'

class CustomizedUserAdmin(UserAdmin):
    inlines = (PerzonalizedUserInline, )

admin.site.unregister(User)
admin.site.register(User, CustomizedUserAdmin)