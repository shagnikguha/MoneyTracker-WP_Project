from django import forms
from django.utils.timezone import now

class InputForm(forms.Form):
    transaction_choices = [
        ("Expense", "Expense"),
        ("Income", "Income")
    ]

    category_choices = [
        ("Food", "Food"),
        ("Travel", "Travel"),
        ("Shopping", "Shopping"),
        ("Necessities", "Necessities"),
        ("Entertainment", "Entertainment"),
        ("Other", "Other")
    ]
    
    amount = forms.DecimalField(max_digits=10, decimal_places=2,help_text='Enter the amount (e.g., 25.99)')
    transaction_type = forms.ChoiceField(choices=transaction_choices)
    category = forms.ChoiceField(choices=category_choices, initial='Other')
    date = forms.DateField(initial=now)
    
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':5, 'cols':20}), max_length=200, required=False)
    recurring = forms.BooleanField(required=False, label='Is this a recurring transaction?', help_text='Check this if the transaction repeats regularly')
    
    def save(self, user):
        from .models import Transaction

        transaction = Transaction(
            user=user,
            amount=self.cleaned_data['amount'],
            transaction_type=self.cleaned_data['transaction_type'],
            category=self.cleaned_data['category'],
            date=self.cleaned_data['date'],
            description=self.cleaned_data['description'],
            recurring=self.cleaned_data['recurring']
        )
        transaction.save()
        return transaction
