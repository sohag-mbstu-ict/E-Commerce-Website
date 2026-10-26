from rest_framework import serializers

from .models import Category, Product, ProductImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'image', 'description',
            'is_active', 'product_count',
        ]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'sort_order']


class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    label = serializers.CharField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'attributes', 'label', 'price_adjustment', 'price',
            'stock', 'in_stock', 'image', 'is_active',
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used for list/browse endpoints."""
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'short_description', 'thumbnail',
            'price', 'discount_price', 'current_price', 'discount_percent',
            'stock', 'in_stock', 'is_featured', 'average_rating', 'review_count',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer including images and variants, used for the detail endpoint."""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    frequently_bought_with = ProductListSerializer(many=True, read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'category', 'description', 'short_description',
            'thumbnail', 'images', 'variants', 'frequently_bought_with', 'price', 'discount_price',
            'current_price', 'discount_percent', 'stock', 'in_stock', 'is_active', 'is_featured',
            'average_rating', 'review_count', 'created_at', 'updated_at',
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    """Used by admin/staff to create or update products."""

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'slug', 'sku', 'description', 'short_description',
            'thumbnail', 'price', 'discount_price', 'stock', 'is_active', 'is_featured',
        ]
        read_only_fields = ['id', 'slug']

    def validate(self, attrs):
        price = attrs.get('price', getattr(self.instance, 'price', None))
        discount_price = attrs.get('discount_price', getattr(self.instance, 'discount_price', None))
        if discount_price and price and discount_price >= price:
            raise serializers.ValidationError(
                {'discount_price': 'Discount price must be lower than the regular price.'}
            )
        return attrs
