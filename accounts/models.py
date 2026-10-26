from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with e-commerce specific profile fields."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='Bangladesh')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def full_address(self):
        parts = [self.address_line, self.city, self.postal_code, self.country]
        return ', '.join([p for p in parts if p])
