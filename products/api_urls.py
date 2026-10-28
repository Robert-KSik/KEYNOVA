
from django.urls import path

from .api_views import ProductListAPIView, ProductDetailAPIView
from .api_views import VariantPricePreviewAPIView


urlpatterns = [
    path("products/", ProductListAPIView.as_view(), name="api-product-list"),
    path(
        "products/<int:pk>/",
        ProductDetailAPIView.as_view(),
        name="api-product-detail",
    ),
    path(
    "variants/<int:variant_id>/price/",
    VariantPricePreviewAPIView.as_view(),
    name="variant-price-preview",
),
]
