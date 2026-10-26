from django.core.management.base import BaseCommand

from storefront.models import ContentBlock

HERO_SLIDES = [
    ('Mega Sale - Up to 40% Off', 'On selected styles, for a limited time.', 'Shop Now',
     '/products/', '#111827', '#374151'),
    ('Sharee Collection', 'Jamdani, Katan, Tangail and more - timeless elegance for every occasion.',
     'Shop Sharee', '/products/?category=sharee', '#7f1d1d', '#dc2626'),
    ('3 Piece Collection', 'Lawn, cotton and party wear - comfortable, stylish and ready to wear.',
     'Shop 3 Piece', '/products/?category=3-piece', '#581c87', '#a855f7'),
    ('Bangle Collection', 'Gold plated, kundan and glass churi to complete your look.',
     'Shop Bangles', '/products/?category=bangles', '#78350f', '#d97706'),
    ('Watch Collection', 'Elegant watches for everyday style.',
     'Shop Watches', '/products/?category=watches', '#0f172a', '#475569'),
]

PROMO_BANNERS = [
    ('Find Your Nearest Store', 'Track outlets and pickup points near you.', 'Find a Store',
     '/pages/our-outlet/', '#065f46', '#10b981'),
]


class Command(BaseCommand):
    help = 'Seeds homepage hero-slider slides and promo banners with gradient placeholders.'

    def handle(self, *args, **options):
        created = 0
        for i, (heading, subheading, cta_text, cta_url, start, end) in enumerate(HERO_SLIDES):
            _, was_created = ContentBlock.objects.get_or_create(
                heading=heading,
                block_type=ContentBlock.BlockType.HERO_SLIDE,
                defaults={
                    'subheading': subheading, 'cta_text': cta_text, 'cta_url': cta_url,
                    'color_start': start, 'color_end': end, 'sort_order': i,
                },
            )
            created += int(was_created)

        for i, (heading, subheading, cta_text, cta_url, start, end) in enumerate(PROMO_BANNERS):
            _, was_created = ContentBlock.objects.get_or_create(
                heading=heading,
                block_type=ContentBlock.BlockType.PROMO_BANNER,
                defaults={
                    'subheading': subheading, 'cta_text': cta_text, 'cta_url': cta_url,
                    'color_start': start, 'color_end': end, 'sort_order': i,
                },
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f'Created {created} homepage content block(s).'))
