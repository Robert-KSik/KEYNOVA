from django.contrib import admin
from .models import Brand, Category, Product

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display =("name","website")
    search_fields = ("name",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display =("name",)
    search_fields =("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "price",
        "stock",
        "is_available",     
        
        )
    list_filter = ("brand", "category", "is_available")
    search_fields = ("name", "brand__name")
    list_editable = ("price", "stock", "is_available")

