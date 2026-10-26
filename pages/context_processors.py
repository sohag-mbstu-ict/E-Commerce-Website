from .models import Page


def footer_pages(request):
    """Makes footer link pages (About, FAQ, policies, etc.) available on every page."""
    return {'footer_pages': Page.objects.filter(show_in_footer=True, is_published=True)}
