from django.contrib import admin

from .models import Category, Product, ProductImage, ProductVariant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'category')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    list_editable = ('price', 'discount_price', 'stock', 'is_active', 'is_featured')
    filter_horizontal = ('frequently_bought_with',)
    fieldsets = (
        (None, {'fields': ('category', 'name', 'slug', 'sku', 'thumbnail')}),
        ('Pricing & stock', {'fields': ('price', 'discount_price', 'stock')}),
        ('Description', {'fields': ('short_description', 'description')}),
        ('Product details', {
            'fields': ('material', 'fit', 'care_instructions'),
            'description': 'Shown under "Product details" and "Care instructions" on the product page.',
        }),
        ('Visibility', {'fields': ('is_active', 'is_featured')}),
        ('Cross-sell', {'fields': ('frequently_bought_with',), 'classes': ('collapse',)}),
    )
