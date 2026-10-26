from .utils import get_or_create_cart


class CartMiddleware:
    """Attaches `request.cart` to every request so templates/views can use it directly."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.cart = SimpleLazyCart(request)
        return self.get_response(request)


class SimpleLazyCart:
    """Lazily resolves the cart only if something actually accesses it."""

    def __init__(self, request):
        self._request = request
        self._cart = None

    def _resolve(self):
        if self._cart is None:
            self._cart = get_or_create_cart(self._request)
        return self._cart

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __str__(self):
        return str(self._resolve())
