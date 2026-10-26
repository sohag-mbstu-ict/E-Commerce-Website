from .models import Category


def categories(request):
    """Makes the active category list available to every template (for the nav menu)."""
    return {'nav_categories': Category.objects.filter(is_active=True, parent__isnull=True)}
