from django.urls import path

from .views import (
    AdminOrderStatusUpdateView, CheckoutView, OrderCancelView, OrderDetailView, OrderListView,
)

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('', OrderListView.as_view(), name='list'),
    path('<str:order_number>/', OrderDetailView.as_view(), name='detail'),
    path('<str:order_number>/cancel/', OrderCancelView.as_view(), name='cancel'),
    path('<str:order_number>/status/', AdminOrderStatusUpdateView.as_view(), name='status-update'),
]
