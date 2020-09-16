from django.contrib import admin

# Register your models here.
from .models import Item, OrderItem, Order, Payment, Coupon


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'ordered', 'start_date', 'being_delivered', 'order_delivered',
        'refund_requested', 'refund_granted', 'billing_address', 'payment',
        'coupon', 'refund_requested', 'refund_granted', 'reference_code'
    ]
    list_display_links = ['user', 'billing_address', 'payment', 'coupon']

    list_filter = [
        'user', 'ordered', 'start_date', 'being_delivered', 'order_delivered',
        'refund_requested', 'refund_granted'
    ]

    search_fields = ['user__username', 'reference_code']


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
