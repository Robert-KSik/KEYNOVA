from django.db.models import Count, Prefetch, Q

from .models import Brand, Product, ProductVariant

IN_STOCK = Q(products__is_available=True, products__stock__gt=0)


def brands_with_counts():
    return Brand.objects.annotate(
        product_count=Count("products", filter=IN_STOCK)
    ).order_by("name")


def featured_brands():
    return brands_with_counts().filter(is_featured=True).order_by(
        "featured_order", "name"
    )


def find_brand(slug):
    if not slug:
        return None
    for brand in Brand.objects.all():
        if brand.slug == slug:
            return brand
    return None


def catalog_products(brand=None):
    available_variants = ProductVariant.objects.filter(
        is_available=True,
        stock__gt=0,
    ).order_by("price_adjustment", "variant_name")

    products = (
        Product.objects.filter(is_available=True, stock__gt=0)
        .select_related("brand", "category")
        .prefetch_related(Prefetch("variants", queryset=available_variants))
        .order_by("id")
    )
    if brand is not None:
        products = products.filter(brand=brand)
    return products