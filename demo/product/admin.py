from django.contrib import admin

from .models import Category, Product


class ProductInline(admin.TabularInline):
    model = Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [ProductInline, ]
