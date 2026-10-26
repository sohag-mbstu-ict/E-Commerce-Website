from .models import Cart

GUEST_CART_SESSION_KEY = 'guest_cart_id'


def get_or_create_cart(request):
    """
    Returns the Cart for the current request:
    - authenticated user -> Cart tied to their account
    - anonymous -> Cart tied to their session key (session created if needed)
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    request.session[GUEST_CART_SESSION_KEY] = cart.pk
    return cart


def get_existing_cart(request):
    """Like get_or_create_cart, but read-only: returns None instead of creating a cart/session."""
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    session_key = request.session.session_key
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key, user=None).first()


def merge_session_cart_into_user(request, user):
    """
    Call this right after login so a guest's cart isn't lost.

    Django's login() rotates the session key but keeps the session data, so the
    guest cart is found via the id stored in the session, falling back to the
    current session key.
    """
    guest_cart = None
    guest_cart_id = request.session.get(GUEST_CART_SESSION_KEY)
    if guest_cart_id:
        guest_cart = Cart.objects.filter(pk=guest_cart_id, user=None).first()
    if not guest_cart and request.session.session_key:
        guest_cart = Cart.objects.filter(session_key=request.session.session_key, user=None).first()
    request.session.pop(GUEST_CART_SESSION_KEY, None)
    if not guest_cart:
        return
    user_cart, _ = Cart.objects.get_or_create(user=user)
    user_cart.merge_from(guest_cart)
