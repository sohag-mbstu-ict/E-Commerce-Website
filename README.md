# MyShop — Django REST Framework E-commerce Starter

A single-vendor e-commerce backend built with **Django + Django REST Framework**, plus a simple
Bootstrap 5 storefront (server-rendered templates) so the site works out of the box without a
separate frontend.

## Features

- **Auth**: JWT (via `djangorestframework-simplejwt`) for the API, session auth for the storefront/admin
- **Catalog**: categories, products, product images, variants (size/color via flexible JSON attributes)
- **Cart**: works for guests (session-based) and logged-in users; guest cart merges into the
  account automatically on login
- **Checkout & Orders**: stock validation, price snapshotting, automatic shipping-fee calculation,
  order status tracking history
- **Reviews & ratings**: with automatic "verified purchase" detection
- **Wishlist**: save products for later (requires login); API + storefront pages
- **Compare**: side-by-side product comparison, works for guests via session (up to 4 products)
- **Frequently Bought Together**: admin-curated cross-sell shown on the product page with a
  one-click "Add All to Cart"
- **CMS-lite pages**: editable About/Contact/FAQ/policy pages shown in the footer (`pages` app)
- **Editable homepage content**: hero slider + promo banners are `ContentBlock` records you edit
  from the Django admin - no template changes needed to update headlines, CTAs or gradient colors
- **Admin dashboard API**: revenue summary, order stats, low-stock alerts, top products
- **Django admin**: full CRUD for every model out of the box at `/admin/`

## Project layout

```
config/         project settings, root urls, api_urls
accounts/       custom User model, register/profile, JWT login
catalog/        Category, Product, ProductImage, ProductVariant
cart/           Cart, CartItem, session/user cart merging
orders/         Order, OrderItem, OrderStatusHistory, checkout service
reviews/        product Review model + API
wishlist/       WishlistItem model + API
compare/        session-based product comparison (no DB model)
pages/          flat CMS pages (About, FAQ, policies) shown in the footer
dashboard/      admin-only analytics endpoints
storefront/     server-rendered views (home, PDP, cart, checkout, account) + ContentBlock model
templates/      Bootstrap 5 templates used by storefront
static/         CSS
```

## Setup

1. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # edit .env and set a real DJANGO_SECRET_KEY before deploying
   ```

3. **Run migrations and create an admin user**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **(Optional) Load demo content**

   ```bash
   python manage.py seed_demo_data          # sample products, categories, variants
   python manage.py seed_pages              # About/Contact/FAQ/policy footer pages
   python manage.py seed_homepage_content   # hero slider slides + promo banner
   ```

5. **Run the dev server**

   ```bash
   python manage.py runserver
   ```

   - Storefront: http://127.0.0.1:8000/
   - Django admin: http://127.0.0.1:8000/admin/
   - API root: http://127.0.0.1:8000/api/v1/

## API reference (`/api/v1/`)

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `auth/token/` | Obtain JWT access + refresh tokens (returns user profile too) |
| POST | `auth/token/refresh/` | Refresh an access token |
| POST | `accounts/register/` | Create a new account |
| GET/PATCH | `accounts/me/` | View or update the logged-in user's profile |

### Catalog
| Method | Endpoint | Description |
|---|---|---|
| GET | `catalog/categories/` | List categories |
| GET | `catalog/products/` | List/search/filter products — `?search=`, `?category=`, `?min_price=`, `?max_price=`, `?in_stock=`, `?featured=`, `?ordering=` |
| GET | `catalog/products/<slug>/` | Product detail (images, variants, rating) |
| POST/PUT/DELETE | `catalog/products/` | Staff-only create/update/delete |

### Cart (works for guests via session, or logged-in users)
| Method | Endpoint | Description |
|---|---|---|
| GET | `cart/` | View current cart |
| POST | `cart/items/` | Add item `{product_id, variant_id?, quantity}` |
| PATCH | `cart/items/<id>/` | Update quantity |
| DELETE | `cart/items/<id>/` | Remove item |
| DELETE | `cart/clear/` | Empty the cart |

### Orders (JWT required)
| Method | Endpoint | Description |
|---|---|---|
| POST | `orders/checkout/` | Convert cart into an order |
| GET | `orders/` | List my orders |
| GET | `orders/<order_number>/` | Order detail + tracking history |
| POST | `orders/<order_number>/cancel/` | Cancel a pending/processing order |
| PATCH | `orders/<order_number>/status/` | **Staff only** — update status (tracking) |

### Reviews
| Method | Endpoint | Description |
|---|---|---|
| GET | `reviews/?product=<id>` | List reviews for a product |
| POST | `reviews/` | Create a review (JWT required) |

### Wishlist (JWT required)
| Method | Endpoint | Description |
|---|---|---|
| GET | `wishlist/` | List my wishlist items |
| POST | `wishlist/` | Add a product `{product: <id>}` |
| DELETE | `wishlist/?product=<id>` | Remove a product |

Compare has no dedicated API endpoint - it's a storefront-only feature backed by the session
(`compare/` templates + views), mirroring how the guest cart works before login.

### Dashboard (staff only)
| Method | Endpoint | Description |
|---|---|---|
| GET | `dashboard/summary/` | Revenue, order counts, low stock (products and variants), top products |
| GET | `dashboard/recent-orders/` | Latest 20 orders |

## A note on layout inspiration

The homepage/product-page layout (announcement bar, hero slider, category tile grid, promo
banner, per-attribute variant selectors, Buy Now / Wishlist / Compare / Bought Together) was
modeled after common fashion-storefront UX patterns. No original images, logos, or copy were
copied - hero banners and category tiles render as CSS gradient blocks with your own text, and
all footer/policy copy in `seed_pages` is placeholder for you to rewrite. Swap in your own
photography via the `Product.thumbnail` / `ProductImage` fields whenever you're ready.

## Notes & next steps

- **Database**: ships with SQLite for zero-config local dev. For production, set the `DB_*`
  variables in `.env` (see `.env.example`) to point at Postgres/MySQL.
- **Production settings**: with `DJANGO_DEBUG=False` the app refuses to start unless
  `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` are set to real values, and it enables secure
  cookies, HTTPS redirect and HSTS.
- **Stock**: placing an order decrements stock; cancelling it (customer, API or admin) returns
  the stock. Cancelled orders can't be reopened.
- **Prices**: `min_price`/`max_price` filters and price sorting use the sale price when one is set.
- **Tests**: `python manage.py test`
- **Payments**: no payment gateway is wired in yet — orders default to Cash on Delivery.
  `Order.PaymentMethod` already has `bkash` and `card` choices ready; plug in the gateway
  of your choice (SSLCommerz, bKash, Stripe, etc.) inside `orders/services.py`.
- **Media storage**: uses local disk (`/media`) by default. Swap in `django-storages` +
  S3/Cloud Storage for production.
- **Email**: no email backend configured — add order-confirmation emails in
  `orders/services.place_order_from_cart` when you're ready.
