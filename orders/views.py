from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from products.models import ProductVariant, VariantOption
from .forms import CheckoutForm, PaymentProofForm
from .models import Order, OrderItem, OrderItemCustomization
from .payment_info import PAYMENT_ACCOUNTS


def _get_cart_lines(request):
    """Parse cart entries, including selected customization option IDs."""
    cart = request.session.get("cart", {})
    lines = []

    if not isinstance(cart, dict):
        return lines

    for key, value in cart.items():
        try:
            if isinstance(value, dict):
                quantity = int(value.get("quantity", 0))
            else:
                quantity = int(value)

            if quantity < 1:
                continue

            variant_part, separator, options_part = str(key).partition(":")
            variant_id = int(variant_part)

            if variant_id < 1:
                continue

            if not separator or options_part == "standard":
                option_ids = []
            else:
                option_ids = [int(x) for x in options_part.split("-")]

                if (
                    any(x < 1 for x in option_ids)
                    or len(option_ids) != len(set(option_ids))
                ):
                    continue

            lines.append({
                "key": str(key),
                "variant_id": variant_id,
                "option_ids": sorted(option_ids),
                "quantity": quantity,
            })

        except (TypeError, ValueError, AttributeError):
            continue

    return lines


def _get_order_or_404(request, order_id):
    """Only the order's owner (or the guest who just placed it) may view it."""
    order = get_object_or_404(Order, pk=order_id)

    if request.user.is_authenticated:
        if order.customer_id != request.user.pk:
            raise Http404
    elif request.session.get("last_order_id") != order.pk:
        raise Http404

    return order


@require_http_methods(["GET", "POST"])
def checkout(request):
    lines = _get_cart_lines(request)

    if not lines:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    form = CheckoutForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                variant_ids = {line["variant_id"] for line in lines}

                variants = list(
                    ProductVariant.objects
                    .select_for_update()
                    .filter(id__in=variant_ids)
                    .select_related("product")
                    .order_by("id")
                )
                variant_map = {v.id: v for v in variants}

                if len(variant_map) != len(variant_ids):
                    raise ValueError(
                        "Some cart items no longer exist. Please review your cart."
                    )

                option_ids = {
                    option_id
                    for line in lines
                    for option_id in line["option_ids"]
                }

                options = list(
                    VariantOption.objects
                    .select_for_update()
                    .filter(id__in=option_ids)
                    .order_by("id")
                )
                option_map = {option.id: option for option in options}

                if len(option_map) != len(option_ids):
                    raise ValueError(
                        "Some customization options no longer exist. "
                        "Please review your cart."
                    )

                subtotal = Decimal("0.00")
                order_lines = []
                variant_quantities = {}
                option_quantities = {}

                for line in lines:
                    variant = variant_map[line["variant_id"]]
                    quantity = line["quantity"]

                    if (
                        not variant.is_available
                        or not variant.product.is_available
                    ):
                        raise ValueError(
                            f"{variant.variant_name} is no longer available."
                        )

                    selected_options = [
                        option_map[option_id]
                        for option_id in line["option_ids"]
                    ]

                    if any(
                        option.variant_id != variant.id
                        or not option.is_available
                        or option.stock < 1
                        for option in selected_options
                    ):
                        raise ValueError(
                            "A selected customization is unavailable. "
                            "Please review your cart."
                        )

                    option_types = [
                        option.option_type for option in selected_options
                    ]
                    if len(option_types) != len(set(option_types)):
                        raise ValueError(
                            "A configuration contains duplicate option types. "
                            "Please review your cart."
                        )

                    unit_price = variant.effective_price + sum(
                        (option.extra_price for option in selected_options),
                        Decimal("0.00"),
                    )

                    if unit_price < 0:
                        raise ValueError("An item has an invalid price.")

                    variant_quantities[variant.id] = (
                        variant_quantities.get(variant.id, 0) + quantity
                    )

                    for option in selected_options:
                        option_quantities[option.id] = (
                            option_quantities.get(option.id, 0) + quantity
                        )

                    line_total = unit_price * quantity
                    subtotal += line_total

                    order_lines.append({
                        "variant": variant,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                        "options": selected_options,
                    })

                # Check combined quantities when multiple configurations
                # use the same variant or customization option.
                for variant_id, quantity in variant_quantities.items():
                    if variant_map[variant_id].stock < quantity:
                        raise ValueError(
                            f"Not enough stock for "
                            f"{variant_map[variant_id].variant_name}."
                        )

                for option_id, quantity in option_quantities.items():
                    if option_map[option_id].stock < quantity:
                        raise ValueError(
                            f"Not enough stock for customization "
                            f"{option_map[option_id].choice_name}."
                        )

                payment_method = form.cleaned_data["payment_method"]

                order = Order.objects.create(
                    customer=(
                        request.user
                        if request.user.is_authenticated
                        else None
                    ),
                    full_name=form.cleaned_data["full_name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data["phone"],
                    address=form.cleaned_data["address"],
                    city=form.cleaned_data["city"],
                    postal_code=form.cleaned_data["postal_code"],
                    delivery_notes=form.cleaned_data["delivery_notes"],
                    payment_method=payment_method,
                    payment_status=(
                        "unpaid" if payment_method == "cod" else "pending"
                    ),
                    order_status="pending",
                    currency="MMK",
                    subtotal=subtotal,
                    delivery_fee=Decimal("0.00"),
                    total=subtotal,
                )

                for line in order_lines:
                    order_item = OrderItem.objects.create(
                        order=order,
                        variant=line["variant"],
                        product_name=line["variant"].product.name,
                        variant_name=line["variant"].variant_name,
                        unit_price=line["unit_price"],
                        quantity=line["quantity"],
                        line_total=line["line_total"],
                    )

                    for option in line["options"]:
                        OrderItemCustomization.objects.create(
                            order_item=order_item,
                            option_type=option.option_type,
                            choice_name=option.choice_name,
                            extra_price=option.extra_price,
                        )

                # Deduct variant stock once per variant.
                for variant_id, quantity in variant_quantities.items():
                    variant = variant_map[variant_id]
                    variant.stock -= quantity
                    variant.save(update_fields=["stock"])

                # Deduct customization stock as well.
                for option_id, quantity in option_quantities.items():
                    option = option_map[option_id]
                    option.stock -= quantity
                    option.save(update_fields=["stock"])

            request.session["cart"] = {}
            request.session["last_order_id"] = order.pk
            request.session.modified = True

            # Cash on delivery needs no payment step.
            if payment_method == "cod":
                return redirect("orders:order_success", order_id=order.pk)

            return redirect("orders:order_payment", order_id=order.pk)

        except ValueError as exc:
            form.add_error(None, str(exc))

    return render(request, "orders/checkout.html", {"form": form})


@require_http_methods(["GET", "POST"])
def order_payment(request, order_id):
    order = _get_order_or_404(request, order_id)

    # Nothing to pay online for COD, cancelled orders or old card orders.
    if (
        not order.requires_manual_payment
        or order.order_status == "cancelled"
        or order.payment_method not in PAYMENT_ACCOUNTS
    ):
        return redirect("orders:order_success", order_id=order.pk)

    # Already submitted or confirmed: don't allow another submission.
    if order.payment_status in ("submitted", "paid", "paid_demo"):
        return redirect("orders:order_success", order_id=order.pk)

    account = PAYMENT_ACCOUNTS[order.payment_method]
    form = PaymentProofForm(
        request.POST or None,
        request.FILES or None,
        order=order,
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                order.transaction_id = form.cleaned_data["transaction_id"]

                screenshot = form.cleaned_data.get("payment_screenshot")
                if screenshot:
                    order.payment_screenshot = screenshot

                order.payment_status = "submitted"
                order.payment_submitted_at = timezone.now()
                order.save()

        except IntegrityError:
            # Two people submitted the same ID at the same moment.
            form.add_error(
                "transaction_id",
                "This transaction ID has already been used on another order.",
            )
        else:
            messages.success(
                request,
                "Payment details received. We'll check your payment and "
                "confirm your order soon.",
            )
            return redirect("orders:order_success", order_id=order.pk)

    return render(
        request,
        "orders/payment.html",
        {
            "order": order,
            "account": account,
            "form": form,
        },
    )


def order_success(request, order_id):
    order = _get_order_or_404(request, order_id)
    return render(request, "orders/success.html", {"order": order})


@login_required
def order_history(request):
    orders = (
        Order.objects
        .filter(customer=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/order_history.html",
        {"orders": orders},
    )