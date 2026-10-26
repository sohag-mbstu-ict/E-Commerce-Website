from datetime import timedelta

from django.db.models import Count, Exists, OuterRef, Sum
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product, ProductVariant
from orders.models import Order
from orders.serializers import OrderListSerializer

LOW_STOCK_THRESHOLD = 5


class SalesSummaryView(APIView):
    """
    GET /api/v1/dashboard/summary/
    High-level store metrics for an admin dashboard: revenue, order counts,
    today/this-week figures and top selling products.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        paid_orders = Order.objects.exclude(status=Order.Status.CANCELLED)

        total_revenue = paid_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        orders_today = paid_orders.filter(created_at__gte=today_start).count()
        orders_this_week = paid_orders.filter(created_at__gte=week_start).count()
        revenue_this_week = paid_orders.filter(created_at__gte=week_start).aggregate(
            total=Sum('grand_total')
        )['total'] or 0

        status_breakdown = list(
            Order.objects.values('status').annotate(count=Count('id')).order_by('status')
        )

        # Products sold through variants track stock per variant, so their own
        # Product.stock isn't meaningful - report those at the variant level instead.
        has_active_variants = ProductVariant.objects.filter(product=OuterRef('pk'), is_active=True)
        low_stock_products = list(
            Product.objects.filter(is_active=True, stock__lte=LOW_STOCK_THRESHOLD)
            .exclude(Exists(has_active_variants))
            .order_by('stock')
            .values('id', 'name', 'sku', 'stock')[:10]
        )
        low_stock_variants = [
            {
                'id': v.id, 'product_id': v.product_id, 'product_name': v.product.name,
                'sku': v.sku, 'label': v.label, 'stock': v.stock,
            }
            for v in ProductVariant.objects.filter(
                is_active=True, product__is_active=True, stock__lte=LOW_STOCK_THRESHOLD
            ).select_related('product').order_by('stock')[:10]
        ]

        top_products = list(
            Product.objects.filter(order_items__order__in=paid_orders)
            .annotate(units_sold=Sum('order_items__quantity'))
            .order_by('-units_sold')
            .values('id', 'name', 'units_sold')[:5]
        )

        return Response({
            'total_orders': paid_orders.count(),
            'total_revenue': total_revenue,
            'orders_today': orders_today,
            'orders_this_week': orders_this_week,
            'revenue_this_week': revenue_this_week,
            'status_breakdown': status_breakdown,
            'low_stock_products': low_stock_products,
            'low_stock_variants': low_stock_variants,
            'top_products': top_products,
        })


class RecentOrdersView(APIView):
    """GET /api/v1/dashboard/recent-orders/ - latest orders for the admin dashboard feed."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        orders = Order.objects.all().order_by('-created_at')[:20]
        return Response(OrderListSerializer(orders, many=True).data)
