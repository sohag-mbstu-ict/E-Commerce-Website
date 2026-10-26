from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Category, Product
from cart.models import CartItem
from cart.utils import get_or_create_cart, merge_session_cart_into_user
from orders.models import Order
from pages.models import Page
from orders.services import EmptyCartError, InsufficientStockError, place_order_from_cart, update_order_status
from reviews.models import Review
from reviews.utils import is_verified_purchase
from wishlist.models import WishlistItem

from .forms import CheckoutForm, ProfileForm, RegisterForm, ReviewForm
from .models import ContentBlock


# ---------------------------------------------------------------------------
# Storefront browsing
# ---------------------------------------------------------------------------
def home(request):
    featured_products = Product.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
    latest_products = Product.objects.filter(is_active=True).select_related('category')[:8]
    categories = Category.objects.filter(is_active=True, parent__isnull=True)[:9]
    hero_slides = ContentBlock.objects.filter(block_type=ContentBlock.BlockType.HERO_SLIDE, is_active=True)
    promo_banners = ContentBlock.objects.filter(block_type=ContentBlock.BlockType.PROMO_BANNER, is_active=True)
    return render(request, 'storefront/home.html', {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
        'hero_slides': hero_slides,
        'promo_banners': promo_banners,
    })


def _parse_price(value):
    try:
        price = Decimal(value) if value else None
    except InvalidOperation:
        return None
    return price if price is not None and price.is_finite() else None


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category').with_effective_price()

    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(short_description__icontains=query) | Q(description__icontains=query)
        )

    min_price = _parse_price(request.GET.get('min_price'))
    max_price = _parse_price(request.GET.get('max_price'))
    if min_price is not None:
        products = products.filter(effective_price__gte=min_price)
    if max_price is not None:
        products = products.filter(effective_price__lte=max_price)

    sort = request.GET.get('sort', '-created_at')
    sort_fields = {
        'price': 'effective_price', '-price': '-effective_price',
        '-created_at': '-created_at', 'name': 'name',
    }
    if sort in sort_fields:
        products = products.order_by(sort_fields[sort])

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'storefront/product_list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.filter(is_active=True),
        'current_category': category_slug,
        'query': query or '',
        'sort': sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'images', 'variants', 'reviews__user', 'frequently_bought_with'
        ),
        slug=slug, is_active=True,
    )
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    user_has_reviewed = (
        request.user.is_authenticated and Review.objects.filter(product=product, user=request.user).exists()
    )
    is_wishlisted = (
        request.user.is_authenticated and WishlistItem.objects.filter(product=product, user=request.user).exists()
    )

    # Group variant attributes by key (e.g. "size" -> ["S","M","L"], "color" -> ["Black","White"])
    # so the template can render one dropdown per option, similar to most storefronts.
    variant_options = {}
    variants_data = []
    for variant in product.variants.all():
        if not variant.is_active:
            continue
        for key, value in variant.attributes.items():
            variant_options.setdefault(key, [])
            if value not in variant_options[key]:
                variant_options[key].append(value)
        variants_data.append({
            'id': variant.id,
            'attributes': variant.attributes,
            'stock': variant.stock,
            'price': str(variant.price),
            'regular_price': str(product.price + variant.price_adjustment),
        })

    # Products sold through variants keep their stock per variant
    total_stock = sum(v['stock'] for v in variants_data) if variants_data else product.stock

    # Main photo first, then gallery images - drives the thumbnail strip, counter and viewer
    photos = []
    if product.thumbnail:
        photos.append({'url': product.thumbnail.url, 'alt': product.name})
    photos += [{'url': img.image.url, 'alt': img.alt_text or product.name} for img in product.images.all()]

    # Star breakdown for the reviews summary: [(5, count, percent), ..., (1, count, percent)]
    reviews = list(product.reviews.all())
    rating_breakdown = []
    for stars in range(5, 0, -1):
        count = sum(1 for r in reviews if r.rating == stars)
        rating_breakdown.append((stars, count, round(count * 100 / len(reviews)) if reviews else 0))

    review_form = ReviewForm()
    if request.method == 'POST' and request.POST.get('action') == 'add_review':
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to leave a review.')
            return redirect('storefront:login')
        if user_has_reviewed:
            messages.warning(request, 'You have already reviewed this product.')
        else:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.is_verified_purchase = is_verified_purchase(request.user, product)
                review.save()
                messages.success(request, 'Thanks for your review!')
                return redirect('storefront:product_detail', slug=slug)

    return render(request, 'storefront/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'bought_together': product.frequently_bought_with.filter(is_active=True),
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
        'is_wishlisted': is_wishlisted,
        'variant_options': variant_options,
        'variants_data': variants_data,
        'total_stock': total_stock,
        'photos': photos,
        'reviews': reviews,
        'rating_breakdown': rating_breakdown,
        'shipping_fee': int(settings.DEFAULT_SHIPPING_FEE),
        'free_shipping_threshold': int(settings.FREE_SHIPPING_THRESHOLD),
        'return_policy_page': Page.objects.filter(slug='return-refund-policy', is_published=True).first(),
        'size_chart_page': Page.objects.filter(slug='size-chart', is_published=True).first(),
    })


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------
def _parse_quantity(value, default=1):
    """Parse a quantity from form input without crashing on blank/garbage values."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def cart_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'storefront/cart.html', {'cart': cart})


def cart_add(request, product_id):
    if request.method != 'POST':
        return redirect('storefront:product_list')

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    variant_id = request.POST.get('variant_id') or None
    quantity = max(1, _parse_quantity(request.POST.get('quantity')))

    variant = product.variants.filter(pk=variant_id, is_active=True).first() if variant_id else None
    available_stock = variant.stock if variant else product.stock
    if available_stock < 1:
        messages.error(request, f'Sorry, "{product.name}" is out of stock.')
        return redirect(product.get_absolute_url())

    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant, defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity

    if item.quantity > available_stock:
        item.quantity = available_stock
        messages.warning(request, f'Only {available_stock} of "{product.name}" available - adjusted quantity.')
    item.save()

    if request.POST.get('buy_now'):
        return redirect('storefront:checkout')

    messages.success(request, f'Added "{product.name}" to your cart.')
    return redirect(request.POST.get('next') or 'storefront:cart')


def cart_add_bulk(request):
    """Used by the 'Bought Together' section to add several products at once."""
    if request.method != 'POST':
        return redirect('storefront:product_list')

    cart = get_or_create_cart(request)
    product_ids = [pid for pid in request.POST.getlist('product_id') if pid.isdigit()]
    added = 0
    for product_id in product_ids:
        product = Product.objects.filter(pk=product_id, is_active=True).first()
        if not product or not product.in_stock:
            continue
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=None, defaults={'quantity': 1})
        if not created:
            item.quantity = min(item.quantity + 1, product.stock)
            item.save()
        added += 1

    if added:
        messages.success(request, f'Added {added} item(s) to your cart.')
    return redirect(request.POST.get('next') or 'storefront:cart')


def cart_update(request, item_id):
    if request.method != 'POST':
        return redirect('storefront:cart')
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    quantity = _parse_quantity(request.POST.get('quantity'), default=item.quantity)
    if quantity < 1:
        item.delete()
    else:
        item.quantity = min(quantity, item.available_stock)
        item.save()
    return redirect('storefront:cart')


def cart_remove(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('storefront:cart')


# ---------------------------------------------------------------------------
# Checkout & orders
# ---------------------------------------------------------------------------
@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('storefront:product_list')

    initial = {
        'full_name': request.user.get_full_name() or request.user.username,
        'phone': request.user.phone,
        'email': request.user.email,
        'address_line': request.user.address_line,
        'city': request.user.city,
        'postal_code': request.user.postal_code,
        'country': request.user.country or 'Bangladesh',
    }

    if request.method == 'POST':
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            try:
                order = place_order_from_cart(
                    cart,
                    user=request.user,
                    shipping_info=form.cleaned_data,
                    payment_method=form.cleaned_data['payment_method'],
                )
            except (EmptyCartError, InsufficientStockError) as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, f'Order {order.order_number} placed successfully!')
                return redirect('storefront:order_success', order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'storefront/checkout.html', {'form': form, 'cart': cart})


@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'storefront/order_success.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'storefront/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'storefront/order_detail.html', {'order': order})


@login_required
def order_cancel(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status in (Order.Status.PENDING, Order.Status.PROCESSING):
        update_order_status(order, Order.Status.CANCELLED, changed_by=request.user, note='Cancelled by customer.')
        messages.info(request, f'Order {order.order_number} has been cancelled.')
    else:
        messages.error(request, 'This order can no longer be cancelled.')
    return redirect('storefront:order_detail', order_number=order.order_number)


# ---------------------------------------------------------------------------
# Auth & profile
# ---------------------------------------------------------------------------
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        merge_session_cart_into_user(self.request, self.request.user)
        return response


def register(request):
    if request.user.is_authenticated:
        return redirect('storefront:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            merge_session_cart_into_user(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('storefront:home')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('storefront:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'storefront/profile.html', {'form': form})


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------
@login_required
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, f'Removed "{product.name}" from your wishlist.')
    else:
        messages.success(request, f'Added "{product.name}" to your wishlist.')
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'storefront:product_list')


@login_required
def wishlist_list(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('product', 'product__category')
    return render(request, 'storefront/wishlist.html', {'items': items})
