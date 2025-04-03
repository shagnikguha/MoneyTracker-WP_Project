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
