# myapp/models.py
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password

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

class Customer(models.Model):
    username = models.CharField(max_length=20, unique=True)
    email    = models.EmailField(unique=True, blank=True)
    password = models.CharField(max_length=128)  # we’ll hash this manually
    access   = models.CharField(max_length=20, default="Free")

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class Transaction(models.Model):
    user             = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    category         = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="Other")
    date             = models.DateField(default=now)
    description      = models.CharField(max_length=200, blank=True)
    recurring        = models.BooleanField(default=False)
    access           = models.CharField(max_length=20, default="Free")

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} ({self.category})"
