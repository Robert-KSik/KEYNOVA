
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models



class DreamGoal(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dream_goal",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="dream_goals",
    )

    saved_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    daily_savings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def target_price(self):
        return self.variant.effective_price

    @property
    def remaining_amount(self):
        return max(
            Decimal("0.00"),
            self.target_price - self.saved_amount,
        )

    @property
    def progress_percentage(self):
        if self.target_price <= 0:
            return 0

        progress = (self.saved_amount / self.target_price) * 100
        return min(100, float(progress))

    @property
    def days_remaining(self):
        if self.remaining_amount <= 0:
            return 0

        return int(
            (self.remaining_amount / self.daily_savings)
            .to_integral_value(rounding="ROUND_CEILING")
        )

    def __str__(self):
        return f"{self.user} — {self.variant}"



class SavingsEntry(models.Model):
    goal = models.ForeignKey(
        "accounts.DreamGoal",
        on_delete=models.CASCADE,
        related_name="contributions",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    note = models.CharField(
        max_length=200,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.amount} saved on {self.created_at:%Y-%m-%d}"

