from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
from django.db.models import F

from orders.models import Order
from .forms import DreamGoalForm, SavingsContributionForm, ProfileUpdateForm
from .models import DreamGoal


@require_http_methods(["GET", "POST"])
def register_view(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your KEYNOVA account is ready!")
        return redirect("/")

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Welcome back to KEYNOVA!")
        return redirect("/")

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")

    return redirect("/")


@login_required
def account_view(request):
    orders = (
        Order.objects
        .filter(customer=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    dream_goal = (
        DreamGoal.objects
        .filter(user=request.user)
        .select_related("variant", "variant__product")
        .first()
    )

    return render(
        request,
        "accounts/account.html",
        {
            "orders": orders,
            "recent_orders": orders[:3],
            "dream_goal": dream_goal,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            # Keeps the user logged in after the password changes.
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed.")
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})


@login_required
def dream_desk_view(request):
    goal = (
        DreamGoal.objects
        .filter(user=request.user)
        .select_related("variant", "variant__product")
        .first()
    )

    if request.method == "POST":
        form = DreamGoalForm(request.POST, instance=goal)

        if form.is_valid():
            dream_goal = form.save(commit=False)
            dream_goal.user = request.user
            dream_goal.save()

            messages.success(
                request,
                "Your Dream Desk goal has been saved!",
            )
            return redirect("accounts:dream_desk")
    else:
        form = DreamGoalForm(instance=goal)

    return render(
        request,
        "accounts/dream_desk.html",
        {
            "form": form,
            "goal": goal,
        },
    )


@login_required
@require_POST
def add_savings_contribution(request):
    goal = get_object_or_404(
        DreamGoal,
        user=request.user,
    )

    form = SavingsContributionForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.save()

            DreamGoal.objects.filter(pk=goal.pk).update(
                saved_amount=F("saved_amount") + contribution.amount
            )

        messages.success(
            request,
            "Your savings contribution has been recorded!",
        )
    else:
        messages.error(
            request,
            "Please enter a valid contribution amount.",
        )

    return redirect("accounts:dream_desk")