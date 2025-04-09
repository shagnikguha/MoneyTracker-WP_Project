from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

CATEGORY_CHOICES = [
    ("Food", "Food"),
    ("Travel", "Travel"),
    ("Shopping", "Shopping"),
    ("Necessities", "Necessities"),
    ("Entertainment", "Entertainment"),
    ("Other", "Other")
]

TRANSACTION_CHOICES = [
    ("Expense", "Expense"),
    ("Income", "Income")
]

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    date = models.DateField(default=now)
    description = models.CharField(max_length=200, blank=True)
    recurring = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.transaction_type}: {self.amount} ({self.category})"

# New Payment model for PhonePe integration
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_transaction_id = models.CharField(max_length=100, unique=True)  # Renamed from transaction_id
    phonepe_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    associated_transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True)  # Renamed from transaction
    
    def __str__(self):
        return f"Payment: {self.amount} - {self.status}"
    
    
class Subscribed(models.Model):
    user= models.OneToOneField(User,on_delete=models.CASCADE)
    status= models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
