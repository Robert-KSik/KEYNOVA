
from rest_framework import generics

from .models import Product
from .serializers import ProductSerializer
from decimal import Decimal

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProductVariant, VariantOption


class ProductListAPIView(generics.ListAPIView):
    queryset = (
        Product.objects
        .filter(is_available=True)
        .select_related("brand", "category")
    )
    serializer_class = ProductSerializer


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = (
        Product.objects
        .filter(is_available=True)
        .select_related("brand", "category")
    )
    serializer_class = ProductSerializer


class VariantPricePreviewAPIView(APIView):
    """
    Calculate a keyboard's price using trusted database values.
    The browser submits option IDs, never prices.
    """

    def post(self, request, variant_id):
        variant = (
            ProductVariant.objects
            .select_related("product")
            .filter(
                pk=variant_id,
                is_available=True,
                product__is_available=True,
            )
            .first()
        )

        if variant is None:
            return Response(
                {"error": "This keyboard variant is unavailable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        option_ids = request.data.get("option_ids", [])

        if not isinstance(option_ids, list):
            return Response(
                {"error": "option_ids must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(option_ids) != len(set(map(str, option_ids))):
            return Response(
                {"error": "Duplicate option IDs are not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = list(
            VariantOption.objects.filter(
                variant=variant,
                pk__in=option_ids,
                is_available=True,
                stock__gt=0,
            )
        )

        if len(options) != len(option_ids):
            return Response(
                {"error": "One or more options are unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        option_types = [option.option_type for option in options]

        if len(option_types) != len(set(option_types)):
            return Response(
                {"error": "Choose only one option per option type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_price = variant.effective_price
        upgrade_total = sum(
            (option.extra_price for option in options),
            Decimal("0.00"),
        )
        unit_price = base_price + upgrade_total

        return Response({
            "variant_id": variant.pk,
            "product": variant.product.name,
            "base_price": str(base_price),
            "upgrade_total": str(upgrade_total),
            "unit_price": str(unit_price),
            "selected_options": [
                {
                    "id": option.pk,
                    "type": option.option_type,
                    "name": option.choice_name,
                    "extra_price": str(option.extra_price),
                }
                for option in options
            ],
        })
