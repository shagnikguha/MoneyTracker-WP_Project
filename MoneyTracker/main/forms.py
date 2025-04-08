from django import forms
from django.utils.timezone import now
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm 
from .models import Transaction, TRANSACTION_CHOICES, CATEGORY_CHOICES  # Import the choices

class InputForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'category', 'date', 'description', 'recurring']
        
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='Enter the amount (e.g., 25.99)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}) 
    )
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_CHOICES,  # Use module-level variable
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,  # Use module-level variable
        initial='Other',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date = forms.DateField(
        initial=now,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}) 
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        max_length=200, 
        required=False
    )
    
    recurring = forms.BooleanField(
        required=False, 
        label='Is this a recurring transaction?', 
        help_text='Check this if the transaction repeats regularly',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def save(self, user=None, commit=True):
        instance = super().save(commit=False)
        if user:
            instance.user = user
        if commit:
            instance.save()
        return instance

class BootstrapLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class BootstrapRegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'password2':
                field.help_text = 'Enter the same password as before, for verification.'
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({'class': 'form-control'})