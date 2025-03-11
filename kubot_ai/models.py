from django.db import models
from django.contrib.auth import get_user_model
import uuid
import random
import string

# ✅ Task model
class Task(models.Model):
    TASK_TYPES = [
        ('social_media', 'Social Media'),
        ('community', 'Community Engagement'),
        ('partner', 'Partner Activities'),
        ('ethereum', 'Ethereum-Based Tasks'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    reward_amount = models.IntegerField(default=0)  # Reward in native tokens
    partner_project = models.CharField(max_length=255, blank=True, null=True)  # Optional

    def __str__(self):
        return self.title


# ✅ UserTask model to track completed tasks
class UserTask(models.Model):
    user = models.ForeignKey("Wallet", on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    reward_claimed = models.BooleanField(default=False)


# ✅ Reward model to store mining/task rewards
class Reward(models.Model):
    user = models.ForeignKey("Wallet", on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} tokens"


# ✅ Referral model
class Referral(models.Model):
    referrer = models.ForeignKey("Wallet", on_delete=models.CASCADE, related_name="referrals")
    referred_user = models.OneToOneField("Wallet", on_delete=models.CASCADE, related_name="referred_by")
    referral_id = models.CharField(max_length=6, null=True, blank=True)
    reward_amount = models.IntegerField(default=5)  # 5 tokens for first-level referral
    created_at = models.DateTimeField(auto_now_add=True)


# ✅ Wallet model
class Wallet(models.Model):
    
    def generate_referral_id():
        chars = string.ascii_uppercase + string.digits
        unique_part = str(uuid.uuid4().int)[:6]
        random_part = ''.join(random.choices(chars, k=6))
        return f"{random_part[:3]}{unique_part[:3]}"


    
    user = models.CharField(max_length=255, unique=True)
    eth_address = models.CharField(max_length=255, unique=True)
    balance = models.FloatField(default=0.0)
    referral_id = models.CharField(max_length=6, unique=True, editable=False, default=generate_referral_id())

    def __str__(self):
        return f"{self.user} - {self.balance} ETH"
