from django.contrib import admin
from django.utils.html import format_html

from .models import ContentBlock


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ('image_thumb', 'heading', 'block_type', 'sort_order', 'is_active')
    list_display_links = ('image_thumb', 'heading')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('block_type', 'is_active')
    readonly_fields = ('image_preview',)
    fieldsets = (
        (None, {'fields': ('block_type', 'heading', 'subheading', 'cta_text', 'cta_url')}),
        ('Banner picture', {'fields': ('image', 'image_preview')}),
        ('Colors (used when there is no picture)', {'fields': ('color_start', 'color_end', 'text_color')}),
        ('Display', {'fields': ('sort_order', 'is_active')}),
    )

    @admin.display(description='Picture')
    def image_thumb(self, obj):
        if not obj.image:
            return format_html('<div style="width:96px;height:54px;background:{};border-radius:4px"></div>',
                               obj.gradient_css)
        return format_html('<img src="{}" style="width:96px;height:54px;object-fit:cover;border-radius:4px">',
                           obj.image.url)

    @admin.display(description='Current picture')
    def image_preview(self, obj):
        if not obj.image:
            return 'No picture yet - the gradient colors are used.'
        return format_html('<img src="{}" style="max-width:480px;width:100%;border-radius:6px">', obj.image.url)
