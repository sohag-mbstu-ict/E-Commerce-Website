import django_filters
from rest_framework.filters import OrderingFilter

from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    # Filter on the price customers actually pay (sale price when set) - requires the
    # queryset to be annotated via Product.objects.with_effective_price().
    min_price = django_filters.NumberFilter(field_name='effective_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='effective_price', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    featured = django_filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price', 'in_stock', 'featured']

    def filter_in_stock(self, queryset, name, value):
        return queryset.filter(stock__gt=0) if value else queryset.filter(stock=0)


class ProductOrderingFilter(OrderingFilter):
    """Keeps the public `?ordering=price` param, but sorts by the effective (sale-aware) price."""
    field_map = {'price': 'effective_price'}

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering
        mapped = []
        for field in ordering:
            prefix = '-' if field.startswith('-') else ''
            name = field.lstrip('-')
            mapped.append(prefix + self.field_map.get(name, name))
        return mapped
