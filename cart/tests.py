from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product

from .models import Cart, CartItem


class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Shirts')
        self.product = Product.objects.create(category=category, name='Plain Tee', sku='TEE', price=500, stock=5)
        self.sold_out = Product.objects.create(category=category, name='Rare Tee', sku='RARE', price=500, stock=0)
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'pass12345!')

    def test_browsing_does_not_create_carts(self):
        self.client.get(reverse('storefront:home'))
        self.client.get(reverse('storefront:product_list'))
        self.assertEqual(Cart.objects.count(), 0)

    def test_api_add_rejects_cumulative_quantity_over_stock(self):
        client = APIClient()
        self.assertEqual(client.post('/api/v1/cart/items/', {'product_id': self.product.pk, 'quantity': 4}).status_code, 201)
        response = client.post('/api/v1/cart/items/', {'product_id': self.product.pk, 'quantity': 2})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.get().quantity, 4)

    def test_storefront_add_out_of_stock_does_not_create_zero_quantity_line(self):
        self.client.post(reverse('storefront:cart_add', args=[self.sold_out.pk]), {'quantity': 1})
        self.assertFalse(CartItem.objects.filter(product=self.sold_out).exists())

    def test_storefront_bad_quantity_input_does_not_crash(self):
        response = self.client.post(reverse('storefront:cart_add', args=[self.product.pk]), {'quantity': 'abc'})
        self.assertEqual(response.status_code, 302)
        item = CartItem.objects.get()
        self.assertEqual(item.quantity, 1)

        response = self.client.post(reverse('storefront:cart_update', args=[item.pk]), {'quantity': ''})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

        response = self.client.post(reverse('storefront:cart_add_bulk'), {'product_id': ['x', str(self.product.pk)]})
        self.assertEqual(response.status_code, 302)

    def test_guest_cart_merges_on_login_and_respects_stock(self):
        user_cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=user_cart, product=self.product, quantity=3)

        self.client.post(reverse('storefront:cart_add', args=[self.product.pk]), {'quantity': 4})
        self.client.post(reverse('storefront:login'), {'username': 'buyer', 'password': 'pass12345!'})

        self.assertFalse(Cart.objects.filter(user=None).exists())
        self.assertEqual(user_cart.items.get().quantity, 5)  # 3 + 4 capped at stock of 5

    def test_guest_cart_merges_on_register(self):
        self.client.post(reverse('storefront:cart_add', args=[self.product.pk]), {'quantity': 2})
        self.client.post(reverse('storefront:register'), {
            'username': 'newbie', 'email': 'newbie@example.com',
            'password1': 'S3cure-pass-xyz', 'password2': 'S3cure-pass-xyz',
        })
        cart = Cart.objects.get(user__username='newbie')
        self.assertEqual(cart.items.get().quantity, 2)
