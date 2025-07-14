from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

# Register Model
class Register(models.Model):
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    security_question = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

# Profile Model
class Profile(models.Model):
    user = models.OneToOneField(Register, on_delete=models.CASCADE, related_name='profile')
    wallet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=10000000.00)
    photo_url = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self):
        return self.user.username

# Automatically create a Profile when a Register is created
@receiver(post_save, sender=Register)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Transaction Model (For 'Purchase History Table')
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )

    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='transactions')
    coin = models.CharField(max_length=100)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=20, decimal_places=2)
    type = models.CharField(max_length=4, choices=TRANSACTION_TYPES, default='buy')
    purchased_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.type}:: {self.coin}: {self.quantity}"
    
# TokenBalance Model (For Current Token Balances Table)
class TokenBalance(models.Model):
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='token_balances')
    coin = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'coin')

    def __str__(self):
        return f"{self.user.username} - {self.coin}: {self.quantity}"

# Profit-Loss Summary Model
class ProfitLossSummary(models.Model):
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='profit_loss_summary')
    coin = models.CharField(max_length=50)
    
    total_invested = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    total_purchased_quantity = models.PositiveIntegerField(default=0)
    total_sold_quantity = models.PositiveIntegerField(default=0)
    total_earned = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    holding_quantity = models.PositiveIntegerField(default=0)
    current_price = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    holding_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    net_profit_loss = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'coin')
        verbose_name_plural = 'Profit & Loss Summaries'

    def __str__(self):
        return f"{self.user.username} - {self.coin}"
