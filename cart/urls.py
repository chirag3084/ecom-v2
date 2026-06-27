from django.urls import path

from .views import CartView, add_to_cart, decreaseCart, remove_from_cart

app_name = "cart"

urlpatterns = [
    path("", CartView, name="detail"),
    path("add/<slug:slug>/", add_to_cart, name="add"),
    path("remove/<slug:slug>/", remove_from_cart, name="remove"),
    path("decrease/<slug:slug>/", decreaseCart, name="decrease"),
]


