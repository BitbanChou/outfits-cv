import os
from django.db import models
from django.contrib.auth.models import User
from colorsys import rgb_to_hls


def user_model_directory_path(instance, filename):
    # instance.__class__.__name__.lower() → "skintone" or "clothingitem"
    folder = instance.__class__.__name__.lower()
    return os.path.join(
        f"user_{instance.user.username}",
        folder,
        filename
    )

class SkinTone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_model_directory_path)
    color_hex = models.CharField(max_length=7, blank=True)

    class Meta:
        ordering = ['-user']
        indexes = [
            models.Index(fields=['-user']),
        ]

    def __str__(self):
        return f"{self.user.username}'s skin tone"

    def hex_to_hsl(self):
        hex_color = self.color_hex.lstrip('#')

        # Convert hex to RGB 0–255
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # Normalize to 0–1 range
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        # Use colorsys.rgb_to_hls (note: it returns H, L, S)
        h, l, s = rgb_to_hls(r, g, b)

        # Convert H (0-1) to degrees, S & L to percent
        h_deg = round(h * 360)
        s_pct = round(s * 100)
        l_pct = round(l * 100)

        return (h_deg, s_pct, l_pct)

    def get_hue(self):
        return self.hex_to_hsl()[0]


class AccessoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=ClothingItem.Category.ACCESSORY)


class TopManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=ClothingItem.Category.TOP)


class LegsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=ClothingItem.Category.LEGS)


class FeetManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=ClothingItem.Category.FEET)


class ClothingItem(models.Model):
    class Category(models.TextChoices):
        ACCESSORY = 'accessory', 'Accessory'
        TOP  = 'top',  'Top'
        LEGS  = 'legs',  'Legs'
        FEET  = 'feet',  'Feet'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_model_directory_path)
    category = models.CharField(max_length=10, choices=Category)
    color_hex = models.CharField(max_length=7, blank=True)

    objects = models.Manager()
    accessories = AccessoryManager()
    tops = TopManager()
    legs = LegsManager()
    feet = FeetManager()

    class Meta:
        ordering = ['user', 'category']
        indexes = [
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.category} for {self.user.username}"

    def hex_to_hsl(self):
        hex_color = self.color_hex.lstrip('#')

        # Convert hex to RGB 0–255
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # Normalize to 0–1 range
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        # Use colorsys.rgb_to_hls (note: it returns H, L, S)
        h, l, s = rgb_to_hls(r, g, b)

        # Convert H (0-1) to degrees, S & L to percent
        h_deg = round(h * 360)
        s_pct = round(s * 100)
        l_pct = round(l * 100)

        return (h_deg, s_pct, l_pct)

    def get_hue(self):
        return self.hex_to_hsl()[0]
