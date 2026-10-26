from django.urls import path

from .views import CartClearView, CartItemAddView, CartItemDetailView, CartView

app_name = 'cart'

urlpatterns = [
    path('', CartView.as_view(), name='cart'),
    path('items/', CartItemAddView.as_view(), name='item-add'),
    path('items/<int:pk>/', CartItemDetailView.as_view(), name='item-detail'),
    path('clear/', CartClearView.as_view(), name='clear'),
]
