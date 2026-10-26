import uuid

from django.conf import settings
from django.db import models

from catalog.models import Product, ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        CASH_ON_DELIVERY = 'cod', 'Cash on Delivery'
        BKASH = 'bkash', 'bKash'
        CARD = 'card', 'Card'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, null=True
    )

    # Shipping snapshot (kept even if the user later edits their profile)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    note = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH_ON_DELIVERY
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'ORD-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        self.subtotal = sum((item.subtotal for item in self.items.all()), 0)
        self.grand_total = self.subtotal + self.shipping_fee - self.discount_total
        self.save(update_fields=['subtotal', 'grand_total'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.PROTECT)
    variant = models.ForeignKey(
        ProductVariant, related_name='order_items', null=True, blank=True, on_delete=models.SET_NULL
    )

    # Snapshots so historical orders stay accurate even if the product changes later
    product_name = models.CharField(max_length=200)
    variant_label = models.CharField(max_length=150, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class OrderStatusHistory(models.Model):
    """Audit trail so both staff and the customer can see order tracking history."""
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'order status history'

    def __str__(self):
        return f'{self.order.order_number} -> {self.status}'
