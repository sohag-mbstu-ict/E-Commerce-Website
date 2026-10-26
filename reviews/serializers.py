from rest_framework import serializers

from .models import Review
from .utils import is_verified_purchase


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'user', 'user_name', 'rating', 'title', 'comment',
            'is_verified_purchase', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'is_verified_purchase', 'created_at']

    def validate(self, attrs):
        # `user` is read-only, so DRF doesn't apply the (product, user) unique_together check itself.
        user = self.context['request'].user
        product = attrs.get('product') or getattr(self.instance, 'product', None)
        existing = Review.objects.filter(product=product, user=user)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({'product': 'You have already reviewed this product.'})
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        verified = is_verified_purchase(user, validated_data['product'])
        return Review.objects.create(user=user, is_verified_purchase=verified, **validated_data)
