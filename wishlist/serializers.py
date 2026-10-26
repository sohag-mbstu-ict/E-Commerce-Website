from rest_framework import serializers

from catalog.serializers import ProductListSerializer

from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_detail', 'added_at']
        read_only_fields = ['id', 'added_at']
