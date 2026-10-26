from decimal import Decimal

from django.conf import settings
from django.db import transaction

from .models import Order, OrderItem, OrderStatusHistory


class EmptyCartError(Exception):
    pass


class InsufficientStockError(Exception):
    def __init__(self, message, product_name):
        super().__init__(message)
        self.product_name = product_name


class InvalidStatusChangeError(Exception):
    pass


@transaction.atomic
def place_order_from_cart(cart, *, user, shipping_info, payment_method):
    """
    Converts a Cart into an Order:
      - validates stock for every line item
      - snapshots product name/price/variant onto OrderItem
      - decrements product/variant stock
      - records the initial status history entry
      - clears the cart
    Raises EmptyCartError / InsufficientStockError on failure (transaction rolls back).
    """
    items = list(cart.items.select_related('product', 'variant').select_for_update())
    if not items:
        raise EmptyCartError('Your cart is empty.')

    for item in items:
        if item.quantity > item.available_stock:
            raise InsufficientStockError(
                f'Only {item.available_stock} left in stock for {item.product.name}.',
                item.product.name,
            )

    subtotal = sum((item.line_total for item in items), Decimal('0.00'))
    shipping_fee = Decimal('0.00') if subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD)) \
        else Decimal(str(settings.DEFAULT_SHIPPING_FEE))

    order = Order.objects.create(
        user=user,
        full_name=shipping_info['full_name'],
        phone=shipping_info['phone'],
        email=shipping_info.get('email', ''),
        address_line=shipping_info['address_line'],
        city=shipping_info['city'],
        postal_code=shipping_info.get('postal_code', ''),
        country=shipping_info.get('country', 'Bangladesh'),
        note=shipping_info.get('note', ''),
        payment_method=payment_method,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        grand_total=subtotal + shipping_fee,
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            variant=item.variant,
            product_name=item.product.name,
            variant_label=item.variant.label if item.variant else '',
            unit_price=item.unit_price,
            quantity=item.quantity,
        )
        if item.variant:
            item.variant.stock -= item.quantity
            item.variant.save(update_fields=['stock'])
        else:
            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

    OrderStatusHistory.objects.create(order=order, status=Order.Status.PENDING, note='Order placed.')
    cart.items.all().delete()

    return order


def _restock_order_items(order):
    """Return an order's quantities to product/variant stock (used when an order is cancelled)."""
    for item in order.items.select_related('product', 'variant').select_for_update():
        if item.variant:
            item.variant.stock += item.quantity
            item.variant.save(update_fields=['stock'])
        elif not item.variant_label:
            # Plain product line. If the line had a variant that has since been deleted
            # (variant is SET_NULL), there's no stock bucket left to return it to.
            item.product.stock += item.quantity
            item.product.save(update_fields=['stock'])


@transaction.atomic
def update_order_status(order, new_status, *, changed_by=None, note=''):
    """
    Single entry point for status changes so stock and tracking history stay in sync.
    Cancelling returns the items to stock; a cancelled order can't be reopened
    (its stock has already been released and may have been sold again).
    """
    if order.status == Order.Status.CANCELLED and new_status != Order.Status.CANCELLED:
        raise InvalidStatusChangeError('A cancelled order cannot be reopened.')
    if new_status == Order.Status.CANCELLED and order.status != Order.Status.CANCELLED:
        _restock_order_items(order)
    order.status = new_status
    order.save(update_fields=['status', 'updated_at'])
    OrderStatusHistory.objects.create(order=order, status=new_status, changed_by=changed_by, note=note)
    return order
