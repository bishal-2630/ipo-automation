from django.db import models
from django.contrib.auth.models import User

import os

class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meroshare_accounts')
    meroshare_user = models.CharField(max_length=100, unique=True)
    meroshare_pass = models.CharField(max_length=255)  # Should be encrypted in production
    dp_name = models.CharField(max_length=255)
    crn = models.CharField(max_length=20)
    tpin = models.CharField(max_length=10)
    bank_name = models.CharField(max_length=255)
    kitta = models.IntegerField(default=10)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_applied = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.meroshare_user

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
