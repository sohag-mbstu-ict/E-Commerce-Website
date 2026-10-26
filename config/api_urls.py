"""
Central registry for all /api/v1/ endpoints.
"""
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import CustomTokenObtainPairView

urlpatterns = [
    # JWT auth
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('reviews/', include('reviews.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('wishlist/', include('wishlist.urls')),
]
