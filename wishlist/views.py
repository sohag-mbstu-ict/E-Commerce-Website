from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product

from .models import WishlistItem
from .serializers import WishlistItemSerializer


class WishlistView(APIView):
    """GET list / POST add / DELETE (by ?product=<id>) remove."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related('product')
        return Response(WishlistItemSerializer(items, many=True).data)

    def post(self, request):
        product_id = request.data.get('product')
        product = Product.objects.filter(pk=product_id, is_active=True).first()
        if not product:
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        return Response(
            WishlistItemSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        product_id = request.query_params.get('product')
        deleted, _ = WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
        return Response({'deleted': bool(deleted)})
