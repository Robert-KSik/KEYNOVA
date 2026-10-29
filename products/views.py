from django.shortcuts import render, get_object_or_404

from .catalog import brands_with_counts, catalog_products, featured_brands, find_brand
from .models import Product



def home(request):
    brand = find_brand(request.GET.get("brand"))
    return render(
        request,
        "products/home.html",
        {
            "products": catalog_products(brand),
            "featured_brands": featured_brands(),
            "all_brands": brands_with_counts(),
            "active_brand": brand,
        },
    )


def product_cards(request):
    brand = find_brand(request.GET.get("brand"))
    return render(
        request,
        "products/_product_cards.html",
        {
            "products": catalog_products(brand),
            "active_brand": brand,
        },
    )


def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category").prefetch_related("specs"),
        pk=product_id,
        is_available=True,
    )

    variants = product.variants.filter(
        is_available=True,
        stock__gt=0,
    ).order_by("variant_name")

    return render(
        request,
        "products/product_detail.html",
        {"product": product, "variants": variants},
    )