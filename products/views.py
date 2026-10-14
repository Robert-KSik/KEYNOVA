from django.shortcuts import render , get_object_or_404
from .models import Product

def home(request):
    products = Product.objects.filter(
        is_available=True,
        stock__gt=0,
    ).select_related("brand", "category")

    return render(
        request,
        "products/home.html",
        {"products": products} 
    )
def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_available=True
    )

    return render(
        request,
        "products/product_detail.html",
        {"product": product }
    )
