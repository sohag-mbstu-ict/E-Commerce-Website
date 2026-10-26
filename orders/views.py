from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.utils import get_or_create_cart

from .models import Order
from .serializers import (
    CheckoutSerializer, OrderDetailSerializer, OrderListSerializer,
    OrderStatusUpdateSerializer,
)
from .services import (
    EmptyCartError, InsufficientStockError, InvalidStatusChangeError, place_order_from_cart,
    update_order_status,
)


class CheckoutView(APIView):
    """POST /api/v1/orders/checkout/ - convert the current cart into an order."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = get_or_create_cart(request)
        try:
            order = place_order_from_cart(
                cart,
                user=request.user,
                shipping_info=data,
                payment_method=data['payment_method'],
            )
        except EmptyCartError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientStockError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """GET /api/v1/orders/ - the logged-in user's own order history."""
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/v1/orders/<order_number>/ - detail + tracking history for one order."""
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)


class OrderCancelView(APIView):
    """POST /api/v1/orders/<order_number>/cancel/ - customer cancels their own pending order."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_number):
        order = Order.objects.filter(order_number=order_number, user=request.user).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        if order.status not in (Order.Status.PENDING, Order.Status.PROCESSING):
            return Response(
                {'detail': f'Orders that are already {order.status} cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        update_order_status(order, Order.Status.CANCELLED, changed_by=request.user, note='Cancelled by customer.')
        return Response(OrderDetailSerializer(order).data)


class AdminOrderStatusUpdateView(APIView):
    """PATCH /api/v1/orders/<order_number>/status/ - staff updates order status (tracking)."""
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, order_number):
        order = Order.objects.filter(order_number=order_number).first()
        if not order:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            update_order_status(
                order,
                serializer.validated_data['status'],
                changed_by=request.user,
                note=serializer.validated_data.get('note', ''),
            )
        except InvalidStatusChangeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderDetailSerializer(order).data)
