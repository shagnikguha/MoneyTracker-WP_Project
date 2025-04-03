from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Transaction
from .forms import InputForm

from django.contrib import messages

def auth_view(request):
    login_form = AuthenticationForm()
    register_form = UserCreationForm()
    
    if request.method == 'POST':
        if 'login_submit' in request.POST:
            # Process login form
            login_form = AuthenticationForm(data=request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f"Welcome back, {username}!")
                    return redirect('today_transactions')
        
        elif 'register_submit' in request.POST:
            # Process registration form
            register_form = UserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                messages.success(request, f"Account created successfully! Welcome, {user.username}!")
                return redirect('today_transactions')
    
    return render(request, 'auth.html', {'login_form': login_form, 'register_form': register_form})

@login_required
def today_transactions_view(request):
    today = timezone.now().date()
    data = Transaction.objects.filter(user=request.user, date=today).order_by('-id')
    
    if request.method == 'POST':
        form = InputForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Transaction added successfully!")
            return redirect('today_transactions')
    else:
        form = InputForm()

    return render(request, 'today_transactions.html', {'form': form,'data': data})

@login_required
def transaction_history_view(request):
    data = Transaction.objects.filter( user=request.user).order_by('-date', '-id')  # Sort by date (newest first), then by ID
    form = InputForm()
    return render(request, 'transaction_history.html', {'form': form, 'data': data})
