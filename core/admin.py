from django.contrib import admin
from .models import SkinTone, ClothingItem


@admin.register(SkinTone)
class SkinToneAdmin(admin.ModelAdmin):
    list_display = ['user', 'color_hex']
    search_fields = ['user']
    list_filter = ['user']
    ordering = ['user']


@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'color_hex']
    search_fields = ['user', 'category']
    list_filter = ['user', 'category']
    ordering = ['user', 'category']