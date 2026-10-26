from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Product

from .utils import MAX_COMPARE_ITEMS, add_to_compare, clear_compare, get_compare_ids, remove_from_compare


def compare_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    ids = get_compare_ids(request)
    if len(ids) >= MAX_COMPARE_ITEMS and product.id not in ids:
        messages.warning(request, f'You can compare up to {MAX_COMPARE_ITEMS} products at a time.')
    else:
        add_to_compare(request, product_id)
        messages.success(request, f'Added "{product.name}" to compare.')
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'storefront:product_list')


def compare_remove(request, product_id):
    remove_from_compare(request, product_id)
    return redirect('compare:view')


def compare_clear(request):
    clear_compare(request)
    return redirect('compare:view')


def compare_view(request):
    ids = get_compare_ids(request)
    products = Product.objects.filter(id__in=ids).prefetch_related('variants')
    # preserve the order the user added them in
    products = sorted(products, key=lambda p: ids.index(p.id))

    # Build a unified set of variant-attribute keys across compared products (e.g. "size", "color")
    attribute_keys = []
    for product in products:
        for variant in product.variants.all():
            for key in variant.attributes.keys():
                if key not in attribute_keys:
                    attribute_keys.append(key)

    return render(request, 'storefront/compare.html', {
        'products': products,
        'attribute_keys': attribute_keys,
        'max_items': MAX_COMPARE_ITEMS,
    })
