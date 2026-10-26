from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Page(models.Model):
    """Simple flat CMS page for About Us, FAQ, policies, etc."""
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    content = models.TextField(help_text='Plain text or basic HTML.')
    show_in_footer = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('pages:detail', kwargs={'slug': self.slug})
