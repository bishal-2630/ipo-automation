from django.db import models
from django.contrib.auth.models import User
from .encryption import encrypt_password, decrypt_password
import os


class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meroshare_accounts')
    meroshare_user = models.CharField(max_length=100, unique=True)
    meroshare_pass = models.CharField(max_length=500)  # stored encrypted
    dp_name = models.CharField(max_length=255)
    crn = models.CharField(max_length=20)
    tpin = models.CharField(max_length=10)
    bank_name = models.CharField(max_length=255)
    kitta = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    last_applied = models.DateTimeField(auto_now=True)

    def set_meroshare_pass(self, plain_password: str):
        self.meroshare_pass = encrypt_password(plain_password)

    def get_meroshare_pass(self) -> str:
        return decrypt_password(self.meroshare_pass)

    def __str__(self):
        return self.meroshare_user


class BankAccount(models.Model):
    SUPPORTED_BANKS = [
        # Commercial Banks (Class A)
        ('agriculture', 'Agriculture Development Bank Ltd.'),
        ('citizens', 'Citizens Bank International Ltd.'),
        ('everest', 'Everest Bank Ltd.'),
        ('global_ime', 'Global IME Bank Ltd.'),
        ('himalayan', 'Himalayan Bank Ltd.'),
        ('kumari', 'Kumari Bank Ltd.'),
        ('laxmi_sunrise', 'Laxmi Sunrise Bank Ltd.'),
        ('machhapuchchhre', 'Machhapuchchhre Bank Ltd.'),
        ('nabil', 'Nabil Bank Ltd.'),
        ('nepal_bank', 'Nepal Bank Ltd.'),
        ('nimb', 'Nepal Investment Mega Bank Ltd.'),
        ('sbi', 'Nepal SBI Bank Ltd.'),
        ('nic_asia', 'NIC Asia Bank Ltd.'),
        ('nmb', 'NMB Bank Ltd.'),
        ('prabhu', 'Prabhu Bank Ltd.'),
        ('prime', 'Prime Commercial Bank Ltd.'),
        ('rbb', 'Rastriya Banijya Bank Ltd.'),
        ('sanima', 'Sanima Bank Ltd.'),
        ('siddhartha', 'Siddhartha Bank Ltd.'),
        ('scb', 'Standard Chartered Bank Nepal Ltd.'),
        
        # Development Banks (Class B - National Level)
        ('garima', 'Garima Bikas Bank Ltd.'),
        ('jyoti', 'Jyoti Bikas Bank Ltd.'),
        ('kamana', 'Kamana Sewa Bikas Bank Ltd.'),
        ('lumbini', 'Lumbini Bikas Bank Ltd.'),
        ('mahalaxmi', 'Mahalaxmi Bikas Bank Ltd.'),
        ('muktinath', 'Muktinath Bikas Bank Ltd.'),
        ('shangrila', 'Shangri-la Bikas Bank Ltd.'),
        ('shine_resunga', 'Shine Resunga Development Bank Ltd.'),
        
        # Other Development Banks
        ('corporate', 'Corporate Development Bank Ltd.'),
        ('excel', 'Excel Development Bank Ltd.'),
        ('green', 'Green Development Bank Ltd.'),
        ('karnali', 'Karnali Development Bank Ltd.'),
        ('miteri', 'Miteri Development Bank Ltd.'),
        ('narayani', 'Narayani Development Bank Ltd.'),
        ('salapa', 'Salapa Bikas Bank Ltd.'),
        ('saptakoshi', 'Saptakoshi Development Bank Ltd.'),
        ('sindhu', 'Sindhu Bikas Bank Ltd.'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    linked_account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='bank_account',
        null=True,
        blank=True,
    )
    bank = models.CharField(max_length=50, choices=SUPPORTED_BANKS, default='nic_asia')
    bank_username = models.CharField(max_length=255)
    bank_password = models.CharField(max_length=500)  # stored encrypted
    created_at = models.DateTimeField(auto_now_add=True)

    def set_bank_password(self, plain_password: str):
        self.bank_password = encrypt_password(plain_password)

    def get_bank_password(self) -> str:
        return decrypt_password(self.bank_password)

    def __str__(self):
        return f"{self.get_bank_display()} — {self.bank_username}"


class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    token = models.TextField(unique=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_id or 'Unknown Device'}"


class ApplicationLog(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    status = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.meroshare_user} - {self.company_name} ({self.status})"
