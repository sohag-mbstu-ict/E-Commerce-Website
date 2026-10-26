from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'show_in_footer', 'is_published', 'sort_order')
    list_editable = ('show_in_footer', 'is_published', 'sort_order')
    prepopulated_fields = {'slug': ('title',)}
