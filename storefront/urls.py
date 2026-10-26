from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'storefront'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/add-bulk/', views.cart_add_bulk, name='cart_add_bulk'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),

    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),

    path('checkout/', views.checkout, name='checkout'),
    path('orders/success/<str:order_number>/', views.order_success, name='order_success'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/cancel/', views.order_cancel, name='order_cancel'),

    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/profile/', views.profile, name='profile'),
]
