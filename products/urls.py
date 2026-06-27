from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import Home, ProductDetail
from products.api.views import *
from cart.api.views import *

app_name = "products"

router = SimpleRouter()
router.register("api/products", ProductAPIView)
router.register("api/category", CategoryAPIView)
router.register("api/cart", CartAPIView)
router.register("api/order", OrderAPIView)

urlpatterns = [
    path("", Home.as_view(), name="home"),
    path("", include(router.urls)),
    path("products/", Home.as_view(), name="list"),
    path("product/<slug>/", ProductDetail.as_view(), name="product"),
]
