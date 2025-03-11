from django.contrib import admin
from .models import Task, UserTask, Reward, Referral, Wallet

admin.site.register(Task)
admin.site.register(UserTask)
admin.site.register(Reward)
admin.site.register(Referral)
admin.site.register(Wallet)
