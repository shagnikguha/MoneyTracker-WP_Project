from django import forms
from django.utils.timezone import now
# Import standard auth forms if you use them (or your custom auth forms)
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm 
from .models import Transaction

# --- Transaction Form (Your existing form, modified) ---

class InputForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'category', 'date', 'description', 'recurring']
        
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
    
    # Added widget=forms.NumberInput with Bootstrap class and step attribute
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='Enter the amount (e.g., 25.99)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}) 
    )
    
    # Added widget=forms.Select with Bootstrap class
    transaction_type = forms.ChoiceField(
        choices=transaction_choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Added widget=forms.Select with Bootstrap class
    category = forms.ChoiceField(
        choices=category_choices, 
        initial='Other',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Added widget=forms.DateInput with Bootstrap class and type='date' for browser native picker
    date = forms.DateField(
        initial=now,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}) 
    )
    
    # Added Bootstrap class to the existing Textarea widget
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), # Reduced rows, Bootstrap handles resizing
        max_length=200, 
        required=False
    )
    
    # Added widget=forms.CheckboxInput with Bootstrap class
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

# --- Authentication Forms (EXAMPLES - Adapt or replace with your actual forms) ---

# Example Login Form (using standard AuthenticationForm)
class BootstrapLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username", # Keep label for accessibility, hide visually if needed via CSS/template
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

# Example Registration Form (using standard UserCreationForm)
class BootstrapRegisterForm(UserCreationForm):
    # You might want to add email, first_name, last_name etc. here
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add 'form-control' class to all fields inherited from UserCreationForm
        for field_name, field in self.fields.items():
            # Ensure password help text is displayed correctly if needed
            if field_name == 'password2':
                 field.help_text = 'Enter the same password as before, for verification.'
            
            # Add form-control class (unless it's a checkbox/radio etc.)
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                 field.widget.attrs.update({'class': 'form-control'})


# --- History Form (Not applicable) ---
# The History page typically displays data and doesn't use a Django form for its main content.
# If you had a filter form on the history page, you would apply similar widget modifications to that form.