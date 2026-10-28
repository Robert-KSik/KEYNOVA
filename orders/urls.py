
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("my-orders/", views.order_history, name="order_history"),
    path(
        "payment/<int:order_id>/",
        views.order_payment,
        name="order_payment",
    ),
    path(
        "success/<int:order_id>/",
        views.order_success,
        name="order_success",
    ),
]