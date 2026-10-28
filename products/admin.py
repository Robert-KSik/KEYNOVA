
from django.contrib import admin
from .models import Brand, Category, Product, ProductVariant, VariantOption

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "featured_order")
    list_editable = ("is_featured", "featured_order")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


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


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    fields = (
        "product",
        "variant_name",
        "image",
        "case_color",
        "keycap_color",
        "keycap_material",
        "switch_type",
        "switch_model",
        "connection_type",
        "layout",
        "battery_capacity_mah",
        "price_adjustment",
        "compare_at_price",
        "stock",
        "is_available",
    )

    list_display = (
        "variant_name",
        "product",
        "switch_type",
        "connection_type",
        "layout",
        "effective_price",
        "compare_at_price",
        "stock",
        "is_available",
    )

    list_filter = (
        "switch_type",
        "keycap_material",
        "connection_type",
        "layout",
        "is_available",
    )

    search_fields = (
        "variant_name",
        "product__name",
        "switch_model",
    )

    list_editable = ("compare_at_price", "stock", "is_available")


@admin.register(VariantOption)
class VariantOptionAdmin(admin.ModelAdmin):
    list_display = (
        "choice_name",
        "variant",
        "option_type",
        "extra_price",
        "stock",
        "is_available",
    )

    list_filter = ("option_type", "is_available")

    search_fields = (
        "choice_name",
        "variant__variant_name",
        "variant__product__name",
    )

    list_editable = ("extra_price", "stock", "is_available")
