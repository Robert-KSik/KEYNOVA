from django import forms

from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        label="Full name",
        widget=forms.TextInput(attrs={
            "placeholder": "Your full name",
            "autocomplete": "name",
        }),
    )

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={
            "placeholder": "you@example.com",
            "autocomplete": "email",
        }),
    )

    phone = forms.CharField(
        max_length=30,
        label="Phone number",
        widget=forms.TextInput(attrs={
            "placeholder": "Phone number with country code",
            "autocomplete": "tel",
        }),
    )

    address = forms.CharField(
        label="Delivery address",
        widget=forms.Textarea(attrs={
            "placeholder": "Street, building, apartment, or delivery address",
            "rows": 3,
            "autocomplete": "street-address",
        }),
    )

    city = forms.CharField(
        max_length=100,
        label="City or township",
        widget=forms.TextInput(attrs={
            "placeholder": "City or township",
            "autocomplete": "address-level2",
        }),
    )

    postal_code = forms.CharField(
        max_length=20,
        required=False,
        label="Postal code (optional)",
        widget=forms.TextInput(attrs={
            "placeholder": "Postal code (optional)",
            "autocomplete": "postal-code",
        }),
    )

    delivery_notes = forms.CharField(
        required=False,
        label="Delivery instructions (optional)",
        widget=forms.Textarea(attrs={
            "placeholder": "Any special delivery instructions?",
            "rows": 2,
        }),
    )

    payment_method = forms.ChoiceField(
        choices=Order.ACTIVE_PAYMENT_METHODS,
        initial="cod",
        label="Choose a payment method",
        widget=forms.RadioSelect,
    )


class PaymentProofForm(forms.Form):
    """Lets a customer submit proof of a manual payment."""

    MAX_SCREENSHOT_MB = 5

    transaction_id = forms.CharField(
        min_length=6,
        max_length=100,
        label="Transaction ID",
        widget=forms.TextInput(attrs={
            "placeholder": "Paste or type your transaction ID",
            "autocomplete": "off",
            "autocapitalize": "characters",
        }),
    )

    payment_screenshot = forms.ImageField(
        required=False,
        label="Payment screenshot (optional)",
        widget=forms.FileInput(attrs={"accept": "image/*"}),
    )

    def __init__(self, *args, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order

    def clean_transaction_id(self):
        transaction_id = " ".join(
            self.cleaned_data["transaction_id"].split()
        )

        duplicate = Order.objects.filter(
            transaction_id__iexact=transaction_id
        )

        if self.order is not None:
            duplicate = duplicate.exclude(pk=self.order.pk)

        if duplicate.exists():
            raise forms.ValidationError(
                "This transaction ID has already been used on another "
                "order. Please check it and try again."
            )

        return transaction_id

    def clean_payment_screenshot(self):
        screenshot = self.cleaned_data.get("payment_screenshot")

        if screenshot and screenshot.size > self.MAX_SCREENSHOT_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"Screenshot is too large. Maximum size is "
                f"{self.MAX_SCREENSHOT_MB} MB."
            )

        return screenshot