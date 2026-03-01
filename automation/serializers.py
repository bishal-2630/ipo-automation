from rest_framework import serializers
from .models import Account, ApplicationLog, FCMToken

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['token', 'device_id']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['owner']

class ApplicationLogSerializer(serializers.ModelSerializer):
    account_user = serializers.CharField(source='account.meroshare_user', read_only=True)
    
    class Meta:
        model = ApplicationLog
        fields = ['id', 'account', 'account_user', 'company_name', 'status', 'remark', 'timestamp']
