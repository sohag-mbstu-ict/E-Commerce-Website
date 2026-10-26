from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from accounts.models import User
from cart.models import Cart, CartItem
from catalog.models import Category, Product, ProductVariant

from .admin import OrderAdmin
from .models import Order
from .services import InvalidStatusChangeError, place_order_from_cart, update_order_status

SHIPPING = {'full_name': 'Test User', 'phone': '0170000000', 'address_line': 'Road 1', 'city': 'Dhaka'}


class OrderStockTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'pass12345!')
        category = Category.objects.create(name='Shirts')
        self.product = Product.objects.create(category=category, name='Plain Tee', sku='TEE', price=500, stock=10)
        self.shirt = Product.objects.create(category=category, name='Polo', sku='POLO', price=800, stock=0)
        self.variant = ProductVariant.objects.create(product=self.shirt, sku='POLO-L', attributes={'size': 'L'}, stock=5)

        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=3)
        CartItem.objects.create(cart=cart, product=self.shirt, variant=self.variant, quantity=2)
        self.order = place_order_from_cart(cart, user=self.user, shipping_info=SHIPPING, payment_method='cod')

    def refresh_stock(self):
        self.product.refresh_from_db()
        self.variant.refresh_from_db()
        return self.product.stock, self.variant.stock

    def test_placing_order_decrements_stock(self):
        self.assertEqual(self.refresh_stock(), (7, 3))

    def test_cancel_restores_stock_once(self):
        update_order_status(self.order, Order.Status.CANCELLED)
        self.assertEqual(self.refresh_stock(), (10, 5))
        # Cancelling again must not double-restock
        update_order_status(self.order, Order.Status.CANCELLED)
        self.assertEqual(self.refresh_stock(), (10, 5))

    def test_cancelled_order_cannot_be_reopened(self):
        update_order_status(self.order, Order.Status.CANCELLED)
        with self.assertRaises(InvalidStatusChangeError):
            update_order_status(self.order, Order.Status.PROCESSING)

    def test_customer_cancel_via_api_restores_stock(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(f'/api/v1/orders/{self.order.order_number}/cancel/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.refresh_stock(), (10, 5))

    def test_admin_status_edit_goes_through_service(self):
        staff = User.objects.create_superuser('admin', 'admin@example.com', 'pass12345!')
        request = RequestFactory().post('/')
        request.user = staff
        model_admin = OrderAdmin(Order, AdminSite())
        form_class = model_admin.get_form(request, self.order, change=True)
        data = {f: getattr(self.order, f) for f in form_class.base_fields if hasattr(self.order, f)}
        data['status'] = Order.Status.CANCELLED
        data['user'] = self.user.pk
        form = form_class(data, instance=self.order)
        self.assertTrue(form.is_valid(), form.errors)
        model_admin.save_model(request, form.save(commit=False), form, change=True)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.refresh_stock(), (10, 5))
        self.assertTrue(self.order.status_history.filter(status=Order.Status.CANCELLED, changed_by=staff).exists())

    def test_free_shipping_above_threshold(self):
        self.assertEqual(self.order.subtotal, Decimal('3100.00'))
        self.assertEqual(self.order.shipping_fee, Decimal('0.00'))  # 3100 >= 2000 free-shipping threshold
