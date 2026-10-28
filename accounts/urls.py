from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("dream-desk/", views.dream_desk_view, name="dream_desk"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.account_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("profile/password/", views.change_password_view, name="change_password"),
    path(
        "dream-desk/add-contribution/",
        views.add_savings_contribution,
        name="add_savings_contribution",
    ),
]