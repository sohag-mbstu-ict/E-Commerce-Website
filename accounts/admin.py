from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Store profile', {'fields': ('phone', 'address_line', 'city', 'postal_code', 'country', 'avatar')}),
    )
