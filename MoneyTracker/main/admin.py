# myapp/admin.py
from django.contrib import admin
from django import forms
from .models import Customer, Transaction
from django.contrib.auth.hashers import make_password

# If you want the admin to hash the password field automatically:
class CustomerAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Enter a password (will be hashed)"
    )

    class Meta:
        model = Customer
        fields = ["username", "email", "password", "access"]

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash the password before saving
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    form = CustomerAdminForm
    list_display = ("username", "email", "access")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "date", "category")
    list_filter  = ("transaction_type", "category", "date")
