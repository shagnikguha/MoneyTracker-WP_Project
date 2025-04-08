# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from .models import Transaction, Customer
from .forms import InputForm


def index_view(request):
    return render(request, 'index.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Ensure a corresponding Customer exists
                Customer.objects.get_or_create(
                    username=user.username,
                    defaults={
                        'email': user.email,
                        'password': user.password,  # store hashed password
                    }
                )
                messages.success(request, f"Welcome back, {username}!")
                return redirect('today_transactions')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create matching Customer
            Customer.objects.create(
                username=user.username,
                email=user.email,
                password=user.password  # already hashed by UserCreationForm
            )
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}!")
            return redirect('today_transactions')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def today_transactions_view(request):
    # Map the logged-in auth.User → your Customer
    customer = get_object_or_404(Customer, username=request.user.username)
    today = timezone.now().date()
    data = Transaction.objects.filter(user=customer, date=today).order_by('-id')

    if request.method == 'POST':
        form = InputForm(request.POST)
        if form.is_valid():
            form.save(user=customer)
            messages.success(request, "Transaction added successfully!")
            return redirect('today_transactions')
    else:
        form = InputForm()

    return render(request, 'today_transactions.html', {
        'form': form,
        'data': data
    })


@login_required
def transaction_history_view(request):
    customer = get_object_or_404(Customer, username=request.user.username)
    data = Transaction.objects.filter(user=customer).order_by('-date', '-id')
    return render(request, 'transaction_history.html', {'data': data})


@login_required
def edit_transaction_view(request, transaction_id):
    customer = get_object_or_404(Customer, username=request.user.username)
    transaction = get_object_or_404(Transaction, id=transaction_id, user=customer)

    if request.method == 'POST':
        form = InputForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save(user=customer)
            messages.success(request, "Transaction updated successfully!")
            return HttpResponseRedirect(
                request.META.get('HTTP_REFERER', reverse('today_transactions'))
            )
    else:
        form = InputForm(instance=transaction)

    return render(request, 'edit_transaction.html', {'form': form})


@login_required
def delete_transaction_view(request, transaction_id):
    customer = get_object_or_404(Customer, username=request.user.username)
    transaction = get_object_or_404(Transaction, id=transaction_id, user=customer)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        return HttpResponseRedirect(
            request.META.get('HTTP_REFERER', reverse('today_transactions'))
        )

    return redirect('today_transactions')


@login_required
def premium(request):
    return render(request, 'premium.html')
