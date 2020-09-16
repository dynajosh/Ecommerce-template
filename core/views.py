from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .forms import CheckoutForm, CouponForm, RefundForm
from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon, Refund
from django.conf import settings
import stripe
stripe_api_key = settings.STRIPE_SECRET_KEY


def home(request):
    context = {'items': Item.objects.all()}
    return render(request, "home-page.html", context)


def products(request):
    context = {'items': Item.objects.all()}
    return render(request, "product-page.html", context)


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            coupon = CouponForm()
            context = {
                'form': form,
                'couponform': coupon,
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout-page.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip_code')
                # same_billing_address = form.cleaned_data.get(
                #     'same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip_code=zip_code)
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
            else:
                messages.warning(request, "Invalid payment option selected")
                return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(request, "You do not have an active request")
            return redirect("order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        # order to be passed into context
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            couponform = CouponForm()
            context = {
                'order': order,
                'couponform': couponform,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, "payment.html", context)
        messages.warning(self.request, "Kindly add a billing address")
        return redirect("core:checkout")

        def post(self, *args, **kwargs):
            order = Order.objects.get(user=self.request.user, ordered=False)
            token = self.request.POST.get('stripeToken')
            amount = int(order.get_total() * 100)
            # creating the payment instance
            try:
                charge = stripe.Charge.create(
                    amount=amount,
                    currency="usd",
                    source=token,
                    description=description,
                    api_key=stripe_api_key
                    # "sk_test_51GwWOwK4taOC5LCGjITvGthLsj0Gex2qKVeyZUN6feAGCSioCpsGwAinVYgbbsZ3KZjZfB5y1R28r6g6FjaBG0wO00susOb6O2"
                )

                charge.save(
                )  # Just aded this line, pulled it out of Stripe's website
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # Setting order items as ordered
                order_items = order.items.all()
                order_items.update(ordered=True)
                for items in order_items:
                    items.save()
                # assigning payment to the order
                order.ordered = True
                order.payment = payment
                oder.save()
                # Redirect after a succesful payment
                messages.success(self.request, "Your Order was successful!")
                return redirect("/")

            # Use Stripe's library to make requests...
            except stripe.error.CardError as e:
                # Since it's a decline, stripe.error.CardError will be caught
                messages.warning(self.request, "Card Error")
                return redirect("/")
            except stripe.error.RateLimitError as e:
                messages.warning(self.request, "Rate Limit Error")
                return redirect("/")
            # Too many requests made to the API too quickly
            except stripe.error.InvalidRequestError as e:
                messages.warning(self.request, "Invalid Request Error")
                return redirect("/")
            # Invalid parameters were supplied to Stripe's API
            except stripe.error.AuthenticationError as e:
                messages.warning(self.request, "Authentication Erroe")
                return redirect("/")
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            except stripe.error.APIConnectionError as e:
                messages.warning(self.request, "Network Error")
                return redirect("/")
            # Network communication with Stripe failed
            except stripe.error.StripeError as e:
                messages.warning(self.request,
                                 "Something Happened, Please try again")
                return redirect("/")
            # Display a very generic error to the user, and maybe send
            # yourself an email
            except Exception as e:
                messages.warning(
                    self.request,
                    "This is a serious error, we have been notified")
                return redirect("/")
            # Something else happened, completely unrelated to Stripe


class HomeView(ListView):
    model = Item
    template_name = "home-page.html"
    paginate_by = 2


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
            return render(self.request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.warning(request, "You do not have an active request")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item,
                                                          user=request.user,
                                                          ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This Item was updated")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This Item was added to your cart")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user,
                                     ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This Item was added to your cart")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,
                                                  user=request.user,
                                                  ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, "This Item was removed from your cart")
            return redirect("core:order-summary")
        else:
            # Add a message saying the order does not contain this order Item
            messages.info(request, "This Item was not in your cart")
            return redirect("core:order-summary")
    else:
        # Add a message saying the user doesn't have an order
        messages.info(request, "You do not have an active order")
        return redirect("core:home")


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,
                                                  user=request.user,
                                                  ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                messages.info(request, "This Item's quantity was updated")
                return redirect("core:order-summary")
            else:
                order.items.remove(order_item)
                messages.info(request, "This Item was removed from your cart")
                return redirect("core:order-summary", slug=slug)
        else:
            # Add a message saying the order does not contain this order Item
            messages.info(request, "This Item was not in your cart")
            return redirect("core:order-summary", slug=slug)
    else:
        # Add a message saying the user doesn't have an order
        messages.info(request, "You do not have an active order")
        return redirect("core:order-summary", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCoupon(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                amount = form.cleaned_data.get('worth')
                order = Order.objects.get(user=self.request.user,
                                          ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Coupon Added Successfully")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.warning(self.request,
                                 "You do not have an active order")
                return redirect("core:checkout")
        # else:
        #     messages.warning(request, "Your Coupon no work")
        # return redirect("core:checkout")


class RequestRefund(View):
    def psot(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            reference_code = form.cleaned_data.get('reference_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # Edit the order
            try:
                order = Order.objects.get(reference_code=reference_code)
                order.refund_requested = True
                order.save()
                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(
                    "Your refund request was received, we'll reach out to you in a jiffy"
                )
                return redirect("/")

            except ObjectDoesNotExist:
                messages.info(
                    self.request,
                    "This order doesn't exist, kindly check the refernce code again"
                )
                return ("/")
