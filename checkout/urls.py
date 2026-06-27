from django.urls import path

from . import views

app_name = "checkout"

urlpatterns = [
    path('checkout/', views.checkout, name="index"),
    path('my-orders/', views.oderView, name="oderView"),
    path("pay/", views.initiate_payment, name="initiate-payment"),
    path("pay/callback/", views.payment_callback, name="payment-callback"),
]
