from django.contrib import admin

from spreedly.models import Subscription, Plan, FeeGroup, Fee, LineItem

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'lifetime', 'active_until', 'active')


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Plan)
admin.site.register(FeeGroup)
admin.site.register(Fee)
admin.site.register(LineItem)
