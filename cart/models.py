from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import Product, ProductVariant


class Cart(models.Model):
    """
    Belongs to a logged-in user OR an anonymous session (session_key).
    Exactly one of the two should be set.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='cart', on_delete=models.CASCADE
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart #{self.pk} ({self.user or self.session_key})'

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal('0.00'))

    def merge_from(self, other_cart):
        """Merge a guest cart into this (now logged-in) user's cart, then delete the guest cart."""
        for item in other_cart.items.select_related('product', 'variant'):
            existing = self.items.filter(product=item.product, variant=item.variant).first()
            if existing:
                # Don't let the merge push the line past what's in stock. (If the item
                # is now out of stock entirely, checkout will reject it with a clear message.)
                existing.quantity = min(existing.quantity + item.quantity, max(existing.available_stock, 1))
                existing.save()
            else:
                item.cart = self
                item.save()
        other_cart.delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'variant')

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def unit_price(self):
        return self.variant.price if self.variant else self.product.current_price

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def available_stock(self):
        return self.variant.stock if self.variant else self.product.stock
