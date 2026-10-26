from datetime import timedelta

from django.db import models
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children', on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0, help_text='Lower numbers appear first in the menu.')

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('storefront:product_list') + f'?category={self.slug}'


class ProductQuerySet(models.QuerySet):
    def with_effective_price(self):
        """Annotate `effective_price` (sale price if set, else price) for filtering/sorting by what customers pay."""
        return self.annotate(effective_price=Coalesce('discount_price', 'price'))


class Product(models.Model):
    objects = ProductQuerySet.as_manager()

    category =models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)

    # Shown in the "Product details" / "Care instructions" sections of the product page
    material = models.CharField(max_length=120, blank=True, help_text='e.g. Pure cotton, Georgette, Gold plated brass')
    fit = models.CharField(max_length=60, blank=True, help_text='e.g. Regular fit, Free size')
    care_instructions = models.TextField(
        blank=True, help_text='One instruction per line, e.g. "Dry clean only".'
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text='Optional sale price. Must be lower than price.'
    )

    stock = models.PositiveIntegerField(default=0)
    thumbnail = models.ImageField(upload_to='products/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    frequently_bought_with = models.ManyToManyField(
        'self', blank=True,
        help_text='Products commonly bought alongside this one (shown in "Bought Together").'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f'{base_slug}-{counter}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('storefront:product_detail', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.price:
            return round((1 - (self.discount_price / self.price)) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_new(self):
        """Shows the "New" badge for products added in the last 30 days."""
        return self.created_at >= timezone.now() - timedelta(days=30)

    @property
    def care_instruction_list(self):
        return [line.strip() for line in self.care_instructions.splitlines() if line.strip()]

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg('rating'))
        return round(agg['rating__avg'] or 0, 1)

    @property
    def review_count(self):
        return self.reviews.count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product.name} image #{self.pk}'


class ProductVariant(models.Model):
    """
    A purchasable variation of a product, e.g. Size=XL / Color=Red.
    `attributes` stores arbitrary option key/value pairs so the schema
    doesn't need to change for new attribute types.
    """
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=64, unique=True)
    attributes = models.JSONField(default=dict, blank=True, help_text='e.g. {"size": "XL", "color": "Red"}')
    price_adjustment = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text='Added to (or subtracted from) the base product price.'
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        attrs = ', '.join(f'{k}: {v}' for k, v in self.attributes.items())
        return f'{self.product.name} ({attrs})' if attrs else f'{self.product.name} variant'

    @property
    def price(self):
        return self.product.current_price + self.price_adjustment

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def label(self):
        return ' / '.join(str(v) for v in self.attributes.values())
