from rest_framework import serializers
from .models import Account, ApplicationLog, FCMToken, BankAccount, BankOTP
from .encryption import encrypt_password


class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['token', 'device_id']


class AccountSerializer(serializers.ModelSerializer):
    # Accept plain password on write, never return it on read
    meroshare_pass = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['owner']

    def create(self, validated_data):
        plain = validated_data.pop('meroshare_pass', None)
        instance = Account(**validated_data)
        if plain:
            instance.set_meroshare_pass(plain)
        # Owner is usually set in perform_create, but we handle it here if passed
        instance.save()
        return instance

    def update(self, instance, validated_data):
        plain = validated_data.pop('meroshare_pass', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if plain:
            instance.set_meroshare_pass(plain)
        instance.save()
        return instance


class BankAccountSerializer(serializers.ModelSerializer):
    # Accept plain password on write, never expose it on read
    bank_password = serializers.CharField(write_only=True, required=True)
    bank_display = serializers.CharField(source='get_bank_display', read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            'id', 'bank', 'bank_display',
            'phone_number', 'bank_password',
            'linked_account', 'created_at',
        ]
        read_only_fields = ['owner', 'created_at']

    def create(self, validated_data):
        plain = validated_data.pop('bank_password')
        instance = BankAccount(**validated_data)
        instance.set_bank_password(plain)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        plain = validated_data.pop('bank_password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if plain:
            instance.set_bank_password(plain)
        instance.save()
        return instance


class ApplicationLogSerializer(serializers.ModelSerializer):
    account_user = serializers.CharField(source='account.meroshare_user', read_only=True)

    class Meta:
        model = ApplicationLog
        fields = ['id', 'account', 'account_user', 'company_name', 'status', 'remark', 'is_read', 'timestamp']
class BankOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankOTP
        fields = ['id', 'account', 'otp_code', 'is_used', 'created_at']
        read_only_fields = ['is_used', 'created_at']
