
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import ProductVariant, VariantOption


def make_cart_item_key(variant_id, option_ids):
    normalized_ids = sorted(set(int(option_id) for option_id in option_ids))
    options_part = "-".join(map(str, normalized_ids)) or "standard"
    return f"{variant_id}:{options_part}"


def parse_cart_item_key(key):
    """Read both legacy numeric keys and customized cart keys."""
    try:
        variant_part, separator, options_part = str(key).partition(":")
        variant_id = int(variant_part)

        if variant_id < 1:
            return None

        if not separator or options_part == "standard":
            option_ids = []
        else:
            option_ids = [int(value) for value in options_part.split("-")]

            if any(value < 1 for value in option_ids):
                return None

            if len(option_ids) != len(set(option_ids)):
                return None

        return variant_id, sorted(option_ids)

    except (TypeError, ValueError):
        return None


def get_configuration(variant, option_ids):
    """Validate selected options and calculate the configuration price."""
    options = list(
        VariantOption.objects.filter(
            variant=variant,
            id__in=option_ids,
        )
    )

    if len(options) != len(option_ids):
        return None

    if any(not option.is_available or option.stock < 1 for option in options):
        return None

    # A configuration can select only one option from each option group.
    option_types = [option.option_type for option in options]

    if len(option_types) != len(set(option_types)):
        return None

    extra_price = sum(
        (option.extra_price for option in options),
        Decimal("0.00"),
    )

    unit_price = variant.effective_price + extra_price

    if unit_price < 0:
        return None

    return options, unit_price


def cart_detail(request):
    cart = request.session.get("cart", {})
    parsed_items = []
    variant_ids = set()

    if isinstance(cart, dict):
        for key, quantity in cart.items():
            parsed = parse_cart_item_key(key)

            if parsed is None:
                continue

            variant_id, option_ids = parsed
            parsed_items.append((key, variant_id, option_ids, quantity))
            variant_ids.add(variant_id)

    variants = ProductVariant.objects.filter(
        id__in=variant_ids
    ).select_related("product")

    variant_map = {variant.id: variant for variant in variants}

    items = []
    valid_cart = {}
    total = Decimal("0.00")

    for old_key, variant_id, option_ids, quantity in parsed_items:
        variant = variant_map.get(variant_id)

        if variant is None:
            continue

        product = variant.product

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity < 1
            or not product.is_available
            or not variant.is_available
            or variant.stock < 1
        ):
            continue

        configuration = get_configuration(variant, option_ids)

        if configuration is None:
            continue

        options, unit_price = configuration

        available_stock = min(
            [variant.stock] + [option.stock for option in options]
        )
        quantity = min(quantity, available_stock)

        if quantity < 1:
            continue

        cart_key = make_cart_item_key(variant.id, option_ids)
        valid_cart[cart_key] = quantity

        subtotal = unit_price * quantity
        total += subtotal

        items.append({
            "product": product,
            "variant": variant,
            "options": options,
            "cart_key": cart_key,
            "quantity": quantity,
            "unit_price": unit_price,
            "available_stock": available_stock,
            "subtotal": subtotal,
        })

    request.session["cart"] = valid_cart

    return render(request, "cart/cart_detail.html", {
        "items": items,
        "total": total,
    })


@require_POST
def add_to_cart(request, variant_id):
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=variant_id,
    )
    product = variant.product
    cart = request.session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect("product_detail", product_id=product.id)

    raw_option_ids = request.POST.getlist("selected_option_ids")

    try:
        option_ids = sorted(set(int(value) for value in raw_option_ids if value))
    except (TypeError, ValueError):
        messages.error(request, "Please select valid customization options.")
        return redirect("product_detail", product_id=product.id)

    configuration = get_configuration(variant, option_ids)

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
    elif (
        not product.is_available
        or not variant.is_available
        or variant.stock < 1
    ):
        messages.error(request, "This configuration is unavailable.")
    elif configuration is None:
        messages.error(
            request,
            "One or more selected options are invalid or unavailable.",
        )
    else:
        options, unit_price = configuration
        available_stock = min(
            [variant.stock] + [option.stock for option in options]
        )
        key = make_cart_item_key(variant.id, option_ids)
        current_quantity = cart.get(key, 0)

        if (
            not isinstance(current_quantity, int)
            or isinstance(current_quantity, bool)
            or current_quantity < 0
        ):
            current_quantity = 0

        if unit_price < 0:
            messages.error(request, "This configuration has an invalid price.")
        elif current_quantity + quantity > available_stock:
            messages.error(request, "That quantity exceeds available stock.")
        else:
            cart[key] = current_quantity + quantity
            request.session["cart"] = cart

            messages.success(
                request,
                f"{product.name} — {variant.variant_name} added to your cart.",
            )
            return redirect("cart:cart_detail")

    return redirect("product_detail", product_id=product.id)


@require_POST
def update_cart(request, cart_key):
    cart = request.session.get("cart", {})
    parsed = parse_cart_item_key(cart_key)

    if not isinstance(cart, dict) or parsed is None:
        messages.error(request, "That cart configuration is invalid.")
        return redirect("cart:cart_detail")

    variant_id, option_ids = parsed
    key = make_cart_item_key(variant_id, option_ids)

    # Support a legacy numeric key when updating an old cart.
    existing_key = key if key in cart else str(variant_id)

    if existing_key not in cart:
        messages.error(request, "That configuration is not in your cart.")
        return redirect("cart:cart_detail")

    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=variant_id,
    )
    configuration = get_configuration(variant, option_ids)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect("cart:cart_detail")

    if quantity < 1:
        cart.pop(existing_key, None)
        messages.success(request, "Item removed from your cart.")
    elif (
        not variant.product.is_available
        or not variant.is_available
        or configuration is None
    ):
        messages.error(request, "That configuration is unavailable.")
    else:
        options, _ = configuration
        available_stock = min(
            [variant.stock] + [option.stock for option in options]
        )

        if quantity > available_stock:
            messages.error(request, "That quantity exceeds available stock.")
        else:
            cart.pop(existing_key, None)
            cart[key] = quantity
            messages.success(request, "Cart updated.")

    request.session["cart"] = cart
    return redirect("cart:cart_detail")


@require_POST
def remove_from_cart(request, cart_key):
    cart = request.session.get("cart", {})

    if isinstance(cart, dict):
        parsed = parse_cart_item_key(cart_key)

        if parsed is not None:
            variant_id, option_ids = parsed
            key = make_cart_item_key(variant_id, option_ids)
            cart.pop(key, None)

            # Also remove the legacy key if this is a standard configuration.
            if not option_ids:
                cart.pop(str(variant_id), None)

        request.session["cart"] = cart

    messages.success(request, "Item removed from your cart.")
    return redirect("cart:cart_detail")
