from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from catalog.models import Category, Product, ProductVariant


class EffectivePriceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Shirts')
        # Listed at 1000 but on sale for 300 - customers pay 300.
        self.sale = Product.objects.create(category=category, name='Sale Tee', sku='SALE', price=1000, discount_price=300)
        self.regular = Product.objects.create(category=category, name='Regular Tee', sku='REG', price=500)

    def api_names(self, params):
        response = APIClient().get('/api/v1/catalog/products/', params)
        self.assertEqual(response.status_code, 200)
        return [p['name'] for p in response.data['results']]

    def test_api_price_filter_uses_sale_price(self):
        self.assertEqual(self.api_names({'max_price': 400}), ['Sale Tee'])

    def test_api_price_ordering_uses_sale_price(self):
        self.assertEqual(self.api_names({'ordering': 'price'}), ['Sale Tee', 'Regular Tee'])
        self.assertEqual(self.api_names({'ordering': '-price'}), ['Regular Tee', 'Sale Tee'])

    def test_storefront_price_filter_and_sort_use_sale_price(self):
        response = self.client.get(reverse('storefront:product_list'), {'max_price': 400})
        self.assertEqual([p.name for p in response.context['page_obj']], ['Sale Tee'])

        response = self.client.get(reverse('storefront:product_list'), {'sort': 'price'})
        self.assertEqual([p.name for p in response.context['page_obj']], ['Sale Tee', 'Regular Tee'])

    def test_storefront_bad_price_input_is_ignored(self):
        response = self.client.get(reverse('storefront:product_list'), {'min_price': 'abc', 'max_price': 'NaN'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 2)


class DashboardLowStockTests(TestCase):
    def test_low_stock_reports_variants(self):
        category = Category.objects.create(name='Shirts')
        polo = Product.objects.create(category=category, name='Polo', sku='POLO', price=800, stock=0)
        ProductVariant.objects.create(product=polo, sku='POLO-L', attributes={'size': 'L'}, stock=2)
        ProductVariant.objects.create(product=polo, sku='POLO-M', attributes={'size': 'M'}, stock=50)
        Product.objects.create(category=category, name='Cap', sku='CAP', price=200, stock=1)

        client = APIClient()
        client.force_authenticate(User.objects.create_superuser('admin', 'a@example.com', 'pass12345!'))
        data = client.get('/api/v1/dashboard/summary/').data

        self.assertEqual([p['name'] for p in data['low_stock_products']], ['Cap'])
        self.assertEqual([v['sku'] for v in data['low_stock_variants']], ['POLO-L'])
