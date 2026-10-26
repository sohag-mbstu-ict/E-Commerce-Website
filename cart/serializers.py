from rest_framework import serializers

from catalog.models import Product, ProductVariant

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    thumbnail = serializers.ImageField(source='product.thumbnail', read_only=True)
    variant_label = serializers.CharField(source='variant.label', read_only=True, default='')
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    available_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_slug', 'thumbnail', 'variant',
            'variant_label', 'quantity', 'unit_price', 'line_total', 'available_stock',
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'items_count', 'subtotal', 'updated_at']


class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(is_active=True), required=False, allow_null=True
    )
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        product = attrs['product_id']
        variant = attrs.get('variant_id')
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({'variant_id': 'This variant does not belong to the given product.'})
        stock = variant.stock if variant else product.stock
        if stock < attrs['quantity']:
            raise serializers.ValidationError({'quantity': f'Only {stock} left in stock.'})
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
