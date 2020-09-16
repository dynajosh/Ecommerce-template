from django.urls import path
from .views import home, products, CheckoutView, HomeView, ItemDetailView, add_to_cart, remove_from_cart, OrderSummaryView, remove_single_item_from_cart, PaymentView, AddCoupon
app_name = 'core'
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("product/<slug>", ItemDetailView.as_view(), name="product"),
    path("checkout", CheckoutView.as_view(), name="checkout"),
    path("order-summary", OrderSummaryView.as_view(), name="order-summary"),
    path("add-to-cart/<slug>/", add_to_cart, name="add-to-cart"),
    path("remove-from-cart/<slug>/", remove_from_cart,
         name="remove-from-cart"),
    path("add-coupon/", AddCoupon.as_view(), name="add-coupon"),
    path("remove-single-item-from-cart/<slug>/",
         remove_single_item_from_cart,
         name="remove-single-item-from-cart"),
    path("payment/<payment_option>/", PaymentView.as_view(), name="payment")
]