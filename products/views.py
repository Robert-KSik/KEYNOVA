
from django.shortcuts import render, get_object_or_404
from .models import Product, ProductVariant
from django.db.models import Prefetch


def home(request):
    available_variants = ProductVariant.objects.filter(
        is_available=True,
        stock__gt=0,
    ).order_by("price_adjustment", "variant_name")

    products = Product.objects.filter(
        is_available=True,
        stock__gt=0,
    ).select_related(
        "brand",
        "category",
    ).prefetch_related(
        Prefetch(
            "variants",
            queryset=available_variants,
        )
    )

    return render(
        request,
        "products/home.html",
        {"products": products},
    )
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category"),
        pk=product_id,
        is_available=True
    )

    variants = product.variants.filter(
        is_available=True,
        stock__gt=0,
    ).order_by("variant_name")

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "variants": variants,
        }
    )
