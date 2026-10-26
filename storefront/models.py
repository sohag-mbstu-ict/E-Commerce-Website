from django.db import models


class ContentBlock(models.Model):
    """
    Editable homepage marketing blocks - hero slider slides and promo banners.
    Rendered as CSS gradient blocks with text overlay (no image assets required),
    so store owners can restyle the homepage entirely from the admin panel.
    """

    class BlockType(models.TextChoices):
        HERO_SLIDE = 'hero', 'Hero slider slide'
        PROMO_BANNER = 'promo', 'Full-width promo banner'

    block_type = models.CharField(max_length=10, choices=BlockType.choices, default=BlockType.HERO_SLIDE)
    heading = models.CharField(max_length=120)
    subheading = models.CharField(max_length=200, blank=True)
    cta_text = models.CharField(max_length=40, blank=True, default='Shop Now')
    cta_url = models.CharField(max_length=255, blank=True, help_text='Relative or absolute URL, e.g. /products/?category=mens')

    color_start = models.CharField(max_length=7, default='#1f2937', help_text='Gradient start, hex e.g. #1f2937')
    color_end = models.CharField(max_length=7, default='#4b5563', help_text='Gradient end, hex e.g. #4b5563')
    text_color = models.CharField(max_length=7, default='#ffffff')

    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'[{self.get_block_type_display()}] {self.heading}'

    @property
    def gradient_css(self):
        return f'linear-gradient(120deg, {self.color_start}, {self.color_end})'
