from .utils import get_existing_cart


def cart(request):
    """
    Exposes the current cart (and its item count) to every template.
    Uses a read-only lookup so simply browsing doesn't create a Cart row/session
    for every anonymous visitor.
    """
    current_cart = get_existing_cart(request)
    return {
        'current_cart': current_cart,
        'cart_items_count': current_cart.items_count if current_cart else 0,
    }
