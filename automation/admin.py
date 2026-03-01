from django.contrib import admin
from .models import Account, ApplicationLog, FCMToken

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('meroshare_user', 'dp_name', 'bank_name', 'last_applied', 'is_active')
    search_fields = ('meroshare_user', 'dp_name')

@admin.register(ApplicationLog)
class ApplicationLogAdmin(admin.ModelAdmin):
    list_display = ('account', 'company_name', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')

@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_id', 'created_at')
