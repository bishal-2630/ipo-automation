from rest_framework import serializers
from .models import Account, ApplicationLog

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class ApplicationLogSerializer(serializers.ModelSerializer):
    account_user = serializers.CharField(source='account.meroshare_user', read_only=True)
    
    class Meta:
        model = ApplicationLog
        fields = ['id', 'account', 'account_user', 'company_name', 'status', 'remark', 'timestamp']
