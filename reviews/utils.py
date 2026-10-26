from orders.models import Order, OrderItem

VERIFIED_ORDER_STATUSES = (Order.Status.PROCESSING, Order.Status.SHIPPED, Order.Status.DELIVERED)


def is_verified_purchase(user, product):
    """True if the user has a non-cancelled, non-pending order containing this product."""
    return OrderItem.objects.filter(
        order__user=user, product=product, order__status__in=VERIFIED_ORDER_STATUSES
    ).exists()
