from django.shortcuts import get_object_or_404, render

from .models import Page


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, 'storefront/page_detail.html', {'page': page})
