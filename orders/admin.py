from django.contrib import admin, messages

from .models import Order, OrderItem, OrderStatusHistory
from .services import InvalidStatusChangeError, update_order_status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'product_name', 'variant_label', 'unit_price', 'quantity')


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'note', 'changed_by', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'full_name', 'phone', 'status', 'payment_status',
        'payment_method', 'grand_total', 'created_at',
    )
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'full_name', 'phone', 'email')
    readonly_fields = ('order_number', 'subtotal', 'grand_total', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    list_editable = ('status', 'payment_status')

    def save_model(self, request, obj, form, change):
        """Route status edits through update_order_status so stock and tracking history stay in sync."""
        if not (change and 'status' in form.changed_data):
            super().save_model(request, obj, form, change)
            return

        new_status = obj.status
        obj.status = form.initial['status']
        super().save_model(request, obj, form, change)
        try:
            update_order_status(obj, new_status, changed_by=request.user, note='Updated from admin.')
        except InvalidStatusChangeError as exc:
            messages.error(request, f'{obj.order_number}: {exc}')
