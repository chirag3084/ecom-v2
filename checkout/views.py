import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt

from cart.models import Cart, Order

from .models import BillingAddress, BillingForm

# Initialize the Razorpay client. Keys come from settings (which read them
# from the environment) - set RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET in your
# .env file. The client is created lazily so importing this module never
# fails even if the keys aren't configured yet (e.g. while running tests).
_razorpay_client = None


def get_razorpay_client():
    global _razorpay_client
    if _razorpay_client is None:
        _razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    return _razorpay_client


@login_required
def checkout(request):
    """Collect/confirm the billing address for the user's active order."""

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if not order_qs.exists():
        messages.warning(request, "You do not have an active order.")
        return redirect("cart:detail")

    order = order_qs.first()
    order_items = order.orderitems.all()
    order_total = order.get_totals()

    saved_address = BillingAddress.objects.filter(user=request.user)
    savedAddress = saved_address.first() if saved_address.exists() else None

    form = BillingForm(instance=savedAddress) if savedAddress else BillingForm()

    if request.method == "POST":
        if savedAddress:
            form = BillingForm(request.POST, instance=savedAddress)
        else:
            form = BillingForm(request.POST)
        if form.is_valid():
            billingaddress = form.save(commit=False)
            billingaddress.user = request.user
            billingaddress.save()
            savedAddress = billingaddress

    context = {
        "form": form,
        "order_items": order_items,
        "order_total": order_total,
        "savedAddress": savedAddress,
    }
    return render(request, "checkout/index.html", context)


@login_required
def oderView(request):
    orders = Order.objects.filter(user=request.user, ordered=True)
    context = {"orders": orders}
    return render(request, "checkout/order.html", context)


@login_required
def initiate_payment(request):
    """Create a Razorpay order for the user's active cart/order and show
    the Razorpay checkout page for it."""

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if not order_qs.exists():
        messages.warning(request, "You do not have an active order.")
        return redirect("cart:detail")

    order = order_qs.first()
    order_total = order.get_totals()

    # Amount must be in the smallest currency unit (e.g. paise for INR).
    amount = int(round(order_total * 100))
    currency = "INR"

    razorpay_order = get_razorpay_client().order.create(
        {
            "amount": amount,
            "currency": currency,
            "payment_capture": "1",  # Auto-capture payment instantly
        }
    )

    # Stash the Razorpay order id on our Order so the callback can find it
    # again once Razorpay redirects/POSTs back to us.
    order.orderId = razorpay_order["id"]
    order.save()

    context = {
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_merchant_key": settings.RAZORPAY_KEY_ID,
        "amount": amount,
        "currency": currency,
    }
    return render(request, "checkout/payment.html", context)


@csrf_exempt
def payment_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    signature = request.POST.get("razorpay_signature", "")

    params_dict = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    try:
        get_razorpay_client().utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        return HttpResponseBadRequest("Payment signature verification failed.")

    order = get_object_or_404(Order, orderId=razorpay_order_id, ordered=False)

    friendly_order_id = get_random_string(
        length=16,
        allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    )
    order.ordered = True
    order.paymentId = payment_id
    order.orderId = f"#{order.user}{friendly_order_id}"
    order.save()

    order.orderitems.update(purchased=True)

    return render(request, "checkout/success.html", {"order": order})
