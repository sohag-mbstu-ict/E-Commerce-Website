from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from .filters import ProductFilter, ProductOrderingFilter
from .models import Category, Product, ProductVariant
from .permissions import IsAdminOrReadOnly
from .serializers import (
    CategorySerializer, ProductDetailSerializer, ProductListSerializer,
    ProductWriteSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class ProductViewSet(viewsets.ModelViewSet):
    """
    Browse, search and filter products. Staff can create/update/delete.

    Query params:
      ?search=shirt
      ?category=sharee
      ?min_price=100&max_price=1000
      ?in_stock=true
      ?featured=true
      ?ordering=price / -price / -created_at
    """
    permission_classes = [IsAdminOrReadOnly]
    # Same backends as REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'], but with an ordering
    # filter that sorts `price` by the sale-aware effective price.
    filter_backends = [DjangoFilterBackend, SearchFilter, ProductOrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'short_description', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'name']
    lookup_field = 'slug'

    def get_queryset(self):
        qs = Product.objects.with_effective_price().select_related('category').prefetch_related(
            'images', 'frequently_bought_with',
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True)),
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(is_active=True)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductWriteSerializer
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
