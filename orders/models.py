from django.conf import settings
from django.db import models


class Order(models.Model):
    PAYMENT_METHODS = [
        ("cod", "Cash on Delivery"),
        ("kbz", "KBZPay"),
        ("wave", "Wave Pay"),
        ("aya", "AYA Pay"),
        ("bank", "Bank Transfer"),
        # Kept only so old orders still display correctly.
        ("card", "Card Payment (old)"),
    ]

    # The methods customers can choose at checkout.
    ACTIVE_PAYMENT_METHODS = [
        method for method in PAYMENT_METHODS if method[0] != "card"
    ]

    ORDER_STATUSES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUSES = [
        ("unpaid", "Unpaid"),
        ("pending", "Awaiting Payment"),
        ("submitted", "Payment Submitted"),
        ("paid_demo", "Demo Payment Confirmed"),
        ("paid", "Paid"),
        ("rejected", "Payment Rejected"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    CURRENCIES = [
        ("MMK", "Myanmar Kyat"),
        ("USD", "US Dollar"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    delivery_notes = models.TextField(blank=True)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default="unpaid",
    )
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUSES,
        default="pending",
    )

    # Manual payment proof (KBZPay, Wave Pay, AYA Pay, bank transfer).
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    payment_screenshot = models.ImageField(
        upload_to="payment_proofs/",
        null=True,
        blank=True,
    )
    payment_submitted_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    currency = models.CharField(
        max_length=3,
        choices=CURRENCIES,
        default="MMK",
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def requires_manual_payment(self):
        return self.payment_method not in ("cod", "card")

    @property
    def currency_label(self):
        return "Ks" if self.currency == "MMK" else self.currency

    def __str__(self):
        return f"Order #{self.pk} — {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    # Store a snapshot so later product price changes
    # don't alter the customer's historical order.
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class OrderItemCustomization(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="customizations",
    )
    option_type = models.CharField(max_length=30)
    choice_name = models.CharField(max_length=100)
    extra_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    def __str__(self):
        return f"{self.order_item} — {self.choice_name}"