from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Order, OrderItem, OrderItemCustomization


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
        "payment_method",
        "payment_status",
        "order_status",
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

    actions = ["mark_as_paid", "mark_as_rejected"]

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

    @admin.action(description="Mark selected orders as PAID")
    def mark_as_paid(self, request, queryset):
        payable = queryset.filter(
            payment_status__in=["submitted", "pending", "rejected"]
        )
        count = payable.count()

        payable.update(payment_status="paid", paid_at=timezone.now())
        payable.filter(order_status="pending").update(
            order_status="confirmed"
        )

        self.message_user(request, f"{count} order(s) marked as paid.")

    @admin.action(description="Reject payment (customer can resubmit)")
    def mark_as_rejected(self, request, queryset):
        rejectable = queryset.filter(payment_status="submitted")
        count = rejectable.count()

        rejectable.update(payment_status="rejected")

        self.message_user(request, f"{count} payment(s) rejected.")


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