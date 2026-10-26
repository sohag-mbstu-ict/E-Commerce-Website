from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartItem
from .serializers import AddCartItemSerializer, CartSerializer, UpdateCartItemSerializer
from .utils import get_or_create_cart


class CartView(APIView):
    """GET /api/v1/cart/ - view the current cart (works for guests via session too)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        return Response(CartSerializer(cart).data)


class CartItemAddView(APIView):
    """POST /api/v1/cart/items/ - add a product (optionally a variant) to the cart."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = get_or_create_cart(request)
        product, variant = data['product_id'], data.get('variant_id')
        item = cart.items.filter(product=product, variant=variant).first()
        new_quantity = (item.quantity if item else 0) + data['quantity']
        available_stock = variant.stock if variant else product.stock
        if new_quantity > available_stock:
            return Response(
                {'detail': f'Only {available_stock} left in stock (you already have '
                           f'{item.quantity if item else 0} in your cart).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item:
            item.quantity = new_quantity
            item.save()
        else:
            CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=new_quantity)

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    """PATCH/DELETE /api/v1/cart/items/<id>/ - update quantity or remove an item."""
    permission_classes = [permissions.AllowAny]

    def _get_item(self, request, pk):
        cart = get_or_create_cart(request)
        return cart.items.filter(pk=pk).first()

    def patch(self, request, pk):
        item = self._get_item(request, pk)
        if not item:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data['quantity']

        if quantity > item.available_stock:
            return Response(
                {'detail': f'Only {item.available_stock} left in stock.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.quantity = quantity
        item.save()
        return Response(CartSerializer(item.cart).data)

    def delete(self, request, pk):
        item = self._get_item(request, pk)
        if not item:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        cart = item.cart
        item.delete()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartClearView(APIView):
    """DELETE /api/v1/cart/clear/ - empty the cart."""
    permission_classes = [permissions.AllowAny]

    def delete(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)
