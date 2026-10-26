from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order, OrderItem

from .models import Review


class ReviewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Shirts')
        self.product = Product.objects.create(category=category, name='Plain Tee', sku='TEE', price=500, stock=5)
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'pass12345!')
        order = Order.objects.create(
            user=self.user, full_name='B', phone='1', address_line='a', city='Dhaka', status=Order.Status.DELIVERED,
        )
        OrderItem.objects.create(order=order, product=self.product, product_name='Plain Tee', unit_price=500)

    def test_storefront_review_sets_verified_purchase(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse('storefront:product_detail', args=[self.product.slug]),
            {'action': 'add_review', 'rating': 5, 'title': 'Great', 'comment': 'Nice'},
        )
        self.assertTrue(Review.objects.get().is_verified_purchase)

    def test_storefront_review_form_errors_are_shown(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('storefront:product_detail', args=[self.product.slug]),
            {'action': 'add_review', 'rating': 9},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['review_form'].errors)

    def test_api_duplicate_review_is_400_not_500(self):
        client = APIClient()
        client.force_authenticate(self.user)
        payload = {'product': self.product.pk, 'rating': 4}
        self.assertEqual(client.post('/api/v1/reviews/', payload).status_code, 201)
        self.assertEqual(client.post('/api/v1/reviews/', payload).status_code, 400)
