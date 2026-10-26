from django.contrib import admin

from .models import ContentBlock


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ('heading', 'block_type', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('block_type', 'is_active')
