from rest_framework import permissions, viewsets

from .models import Review
from .serializers import ReviewSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class ReviewViewSet(viewsets.ModelViewSet):
    """
    List/create/update/delete product reviews.
    ?product=<id> filters reviews for a single product.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Review.objects.select_related('user', 'product')
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

    def perform_create(self, serializer):
        serializer.save()
