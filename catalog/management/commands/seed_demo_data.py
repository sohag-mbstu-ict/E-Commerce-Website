import random

from django.core.management.base import BaseCommand

from catalog.models import Category, Product, ProductVariant

# (name, menu sort order) - the nav menu shows categories in this order.
DEMO_CATEGORIES = [
    ('Sharee', 1),
    ('3 Piece', 2),
    ('Bangles', 3),
    ('Watches', 4),
]

# (name, category, sku, price, discount_price)
DEMO_PRODUCTS = [
    ('Jamdani Cotton Sharee', 'Sharee', 'SHR-JAMDANI', 4500, 3990),
    ('Katan Silk Sharee', 'Sharee', 'SHR-KATAN', 8500, None),
    ('Tangail Tant Sharee', 'Sharee', 'SHR-TANGAIL', 2800, 2450),
    ('Georgette Party Sharee', 'Sharee', 'SHR-GEORGETTE', 5200, None),
    ('Lawn Printed 3 Piece', '3 Piece', 'TPC-LAWN', 2200, 1850),
    ('Embroidered Cotton 3 Piece', '3 Piece', 'TPC-EMBROIDERED', 3400, None),
    ('Georgette Party 3 Piece', '3 Piece', 'TPC-GEORGETTE', 4800, 4200),
    ('Gold Plated Bangle Set', 'Bangles', 'BNG-GOLDPLATED', 1500, 1290),
    ('Glass Churi Set (2 Dozen)', 'Bangles', 'BNG-GLASS', 450, None),
    ('Kundan Stone Bangles', 'Bangles', 'BNG-KUNDAN', 2400, None),
    ('Ladies Rose Gold Watch', 'Watches', 'WCH-ROSEGOLD', 3800, 3299),
    ('Classic Leather Strap Watch', 'Watches', 'WCH-LEATHER', 2100, None),
]

# Default product details per category: (material, fit, care instructions)
CATEGORY_DETAILS = {
    'Sharee': ('Cotton blend', 'Free size (5.5 m with blouse piece)', [
        'Dry clean recommended for the first wash',
        'Hand wash separately in cold water',
        'Do not bleach',
        'Dry in shade',
        'Iron on low to medium heat',
    ]),
    '3 Piece': ('Blended fabric', 'Regular fit', [
        'Wash dark colors separately',
        'Cold water gentle wash',
        'Do not bleach',
        'Do not tumble dry',
        'Dry in shade',
        'Iron on reverse side',
    ]),
    'Bangles': ('Alloy metal', 'Available in multiple sizes', [
        'Keep away from water, perfume and chemicals',
        'Wipe with a soft dry cloth after use',
        'Store separately in a box to avoid scratches',
    ]),
    'Watches': ('Stainless steel case', 'Adjustable strap', [
        'Avoid contact with water unless water resistant',
        'Wipe with a soft dry cloth',
        'Keep away from magnets and extreme heat',
    ]),
}

SHAREE_COLORS =['Red', 'Maroon', 'Royal Blue', 'Green']
THREE_PIECE_SIZES = ['S', 'M', 'L', 'XL']
BANGLE_SIZES = ['2.4', '2.6', '2.8']


class Command(BaseCommand):
    help = 'Seeds the database with demo categories, products and variants for local testing.'

    def handle(self, *args, **options):
        cat_map = {}
        for name, sort_order in DEMO_CATEGORIES:
            cat, _ = Category.objects.update_or_create(name=name, defaults={'sort_order': sort_order})
            cat_map[name] = cat
        self.stdout.write(self.style.SUCCESS(f'Ensured {len(cat_map)} categories.'))

        created = 0
        for name, cat_name, sku, price, discount in DEMO_PRODUCTS:
            if Product.objects.filter(sku=sku).exists():
                continue
            product = Product.objects.create(
                category=cat_map[cat_name],
                name=name,
                sku=sku,
                description=f'{name} - beautifully crafted with quality materials. Perfect for festivals, weddings and everyday elegance.',
                short_description=f'{name}, handpicked for you.',
                price=price,
                discount_price=discount,
                stock=random.randint(5, 60),
                is_featured=random.random() < 0.4,
            )
            if cat_name == 'Sharee':
                self._add_variants(product, 'color', SHAREE_COLORS)
            elif cat_name == '3 Piece':
                self._add_variants(product, 'size', THREE_PIECE_SIZES)
            elif cat_name == 'Bangles':
                self._add_variants(product, 'size', BANGLE_SIZES)
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created} demo products.'))

        # Fill in material/fit/care for products in these categories that don't have them yet
        filled = 0
        for cat_name, (material, fit, care) in CATEGORY_DETAILS.items():
            filled += Product.objects.filter(category=cat_map[cat_name], material='').update(
                material=material, fit=fit, care_instructions='\n'.join(care),
            )
        self.stdout.write(self.style.SUCCESS(f'Filled product details for {filled} product(s).'))
        self.stdout.write(self.style.SUCCESS('Done. Log into /admin/ to add real product images.'))

    def _add_variants(self, product, attribute, values):
        for value in values:
            ProductVariant.objects.create(
                product=product,
                sku=f'{product.sku}-{value.replace(" ", "").replace(".", "").upper()}',
                attributes={attribute: value},
                stock=random.randint(0, 20),
            )
