from django.contrib import admin
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.html import format_html

from products.models import ProductVariant, VariantOption

from .models import Order, OrderItem, OrderItemCustomization


# ---------- the rules, one small function per action ----------
# Each returns True if it changed the order, False if the order
# wasn't in the right state (so nothing is changed by mistake).

def _accept(order):
    if order.order_status == "cancelled":
        return False

    if order.payment_method == "cod":
        if order.order_status != "pending":
            return False
    elif order.requires_manual_payment:
        if order.payment_status != "submitted":
            return False
        order.payment_status = "paid"
        order.paid_at = timezone.now()
    else:
        return False

    if order.order_status == "pending":
        order.order_status = "confirmed"

    order.save(update_fields=[
        "payment_status", "paid_at", "order_status", "updated_at",
    ])
    return True


def _reject(order):
    if order.payment_status != "submitted":
        return False
    order.payment_status = "rejected"
    order.save(update_fields=["payment_status", "updated_at"])
    return True


def _ship(order):
    if order.order_status not in ("confirmed", "processing"):
        return False
    order.order_status = "shipped"
    order.save(update_fields=["order_status", "updated_at"])
    return True


def _deliver(order):
    if order.order_status != "shipped":
        return False
    order.order_status = "delivered"
    fields = ["order_status", "updated_at"]
    # Cash on delivery is paid when the parcel arrives.
    if order.payment_method == "cod" and order.payment_status == "unpaid":
        order.payment_status = "paid"
        order.paid_at = timezone.now()
        fields += ["payment_status", "paid_at"]
    order.save(update_fields=fields)
    return True


@transaction.atomic
def _cancel_and_restock(order):
    if order.order_status in ("cancelled", "shipped", "delivered"):
        return False

    items = order.items.prefetch_related("customizations")
    for item in items:
        ProductVariant.objects.filter(pk=item.variant_id).update(
            stock=F("stock") + item.quantity
        )
        for custom in item.customizations.all():
            VariantOption.objects.filter(
                variant_id=item.variant_id,
                option_type=custom.option_type,
                choice_name=custom.choice_name,
            ).update(stock=F("stock") + item.quantity)

    order.order_status = "cancelled"
    order.save(update_fields=["order_status", "updated_at"])
    return True


# ---------- the admin screens ----------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name",
        "variant_name",
        "unit_price",
        "quantity",
        "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "payment_method",
        "payment_status",
        "transaction_id",
        "order_status",
        "currency",
        "total",
        "created_at",
    )

    list_filter = (
        "payment_status",
        "order_status",
        "payment_method",
        "currency",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
        "transaction_id",
    )

    readonly_fields = (
        "screenshot_preview",
        "payment_submitted_at",
        "paid_at",
        "created_at",
        "updated_at",
    )

    inlines = [OrderItemInline]

    actions = [
        "accept_orders",
        "reject_payments",
        "mark_shipped",
        "mark_delivered",
        "cancel_orders",
    ]

    @admin.display(description="Payment screenshot")
    def screenshot_preview(self, obj):
        if obj.payment_screenshot:
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" style="max-height:260px;border-radius:8px;">'
                "</a>",
                obj.payment_screenshot.url,
            )
        return "No screenshot uploaded"

    def save_model(self, request, obj, form, change):
        # If you set Payment status to "Paid" by hand on the order
        # page, still stamp the time and confirm the order.
        if change and "payment_status" in form.changed_data:
            if obj.payment_status == "paid" and obj.paid_at is None:
                obj.paid_at = timezone.now()
                if obj.order_status == "pending":
                    obj.order_status = "confirmed"
        super().save_model(request, obj, form, change)

    def _run(self, request, queryset, rule, done_word):
        orders = list(queryset)
        done = sum(1 for order in orders if rule(order))
        skipped = len(orders) - done
        message = f"{done} order(s) {done_word}."
        if skipped:
            message += f" {skipped} skipped because of their current status."
        self.message_user(request, message)

    @admin.action(description="Accept selected orders")
    def accept_orders(self, request, queryset):
        self._run(request, queryset, _accept, "accepted")

    @admin.action(description="Reject payment (customer can resubmit)")
    def reject_payments(self, request, queryset):
        self._run(request, queryset, _reject, "rejected")

    @admin.action(description="Mark as shipped")
    def mark_shipped(self, request, queryset):
        self._run(request, queryset, _ship, "marked as shipped")

    @admin.action(description="Mark as delivered")
    def mark_delivered(self, request, queryset):
        self._run(request, queryset, _deliver, "marked as delivered")

    @admin.action(description="Cancel and return items to stock")
    def cancel_orders(self, request, queryset):
        self._run(request, queryset, _cancel_and_restock, "cancelled")


@admin.register(OrderItemCustomization)
class OrderItemCustomizationAdmin(admin.ModelAdmin):
    list_display = (
        "order_item",
        "option_type",
        "choice_name",
        "extra_price",
    )
    list_filter = ("option_type",)
    search_fields = (
        "choice_name",
        "order_item__order__id",
    )