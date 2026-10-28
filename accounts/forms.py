from django import forms
from django.contrib.auth import get_user_model

from .models import DreamGoal, SavingsEntry
from products.models import ProductVariant

User = get_user_model()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if email and (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "This email is already used by another account."
            )

        return email


class DreamGoalForm(forms.ModelForm):
    class Meta:
        model = DreamGoal
        fields = ["variant", "saved_amount", "daily_savings"]
        widgets = {
            "saved_amount": forms.NumberInput(
                attrs={"min": "0", "step": "0.01"}
            ),
            "daily_savings": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["variant"].queryset = (
            ProductVariant.objects.filter(
                is_available=True,
                product__is_available=True,
            )
            .select_related("product")
            .order_by("product__name")
        )

        self.fields["variant"].label = "Choose your dream keyboard"
        self.fields["saved_amount"].min_value = 0
        self.fields["daily_savings"].min_value = 0.01


class SavingsContributionForm(forms.ModelForm):
    class Meta:
        model = SavingsEntry
        fields = ["amount", "note"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Amount saved",
                }
            ),
            "note": forms.TextInput(
                attrs={
                    "maxlength": "200",
                    "placeholder": "e.g. Weekend allowance",
                }
            ),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if amount <= 0:
            raise forms.ValidationError(
                "Your contribution must be greater than zero."
            )

        return amount