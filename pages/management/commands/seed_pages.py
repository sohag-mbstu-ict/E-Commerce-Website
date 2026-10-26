from django.core.management.base import BaseCommand

from pages.models import Page

PAGES = [
    ('About Us', 1, (
        'MyShop is an online store built to make everyday shopping simple - quality products, '
        'fair prices and fast delivery. This is placeholder copy: replace it with your own brand '
        'story from the admin panel (Pages > About Us).'
    )),
    ('Our Store', 2, (
        'Find our outlets and pickup points here. This is a placeholder page - add your store '
        'addresses, maps, and opening hours from the admin panel.'
    )),
    ('Contact Us', 3, (
        'Have a question about an order or a product? Reach us at support@example.com or call '
        '+880-000-000000 (placeholder - update with your real contact details).'
    )),
    ('FAQ', 4, (
        'Frequently asked questions go here - shipping times, payment options, return eligibility, '
        'and so on. Replace this placeholder with your real FAQ content.'
    )),
    ('Return & Refund Policy', 5, (
        'Placeholder return & refund policy. Describe your return window, condition requirements, '
        'and refund timelines here before going live.'
    )),
    ('Terms & Condition', 6, (
        'Placeholder terms and conditions. Add your actual store terms of use before launch.'
    )),
    ('Privacy Policy', 7, (
        'Placeholder privacy policy. Describe what customer data you collect and how it is used '
        'before launch.'
    )),
]


class Command(BaseCommand):
    help = 'Seeds standard footer pages (About, Store, Contact, FAQ, policies) with placeholder copy.'

    def handle(self, *args, **options):
        created = 0
        for title, order, content in PAGES:
            _, was_created = Page.objects.get_or_create(
                title=title, defaults={'content': content, 'sort_order': order}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f'Created {created} new page(s). Edit their content at /admin/pages/page/.'
        ))
