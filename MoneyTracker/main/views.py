# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views  # Add this
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import razorpay
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
                    user=user,
                    defaults={'access': 'Free'}
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
            Customer.objects.get_or_create(
                user=user,
                defaults={'access': 'Free'}
            )
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}!")
            return redirect('today_transactions')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def today_transactions_view(request):
    try:
        customer = request.user.customer  # Safely access customer
    except Customer.DoesNotExist:
        # Fallback in case Customer wasn't created (rare due to login/register logic)
        customer, _ = Customer.objects.get_or_create(user=request.user, defaults={'access': 'Free'})
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
        'data': data,
        'customer': customer  # Pass customer to template for access check
    })


@login_required
def transaction_history_view(request):
    # make sure we have a Customer object just like in today_transactions
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        customer, _ = Customer.objects.get_or_create(
            user=request.user,
            defaults={'access': 'Free'}
        )

    data = Transaction.objects.filter(user=customer).order_by('-date', '-id')
    return render(request, 'transaction_history.html', {
        'data': data,
        'customer': customer,    # ← add this
    })


@login_required
def edit_transaction_view(request, transaction_id):
    customer = request.user.customer
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
    customer = request.user.customer
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
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment_data = {
        'amount': 20000,  # 200 INR in paise
        'currency': 'INR',
        'payment_capture': '1'
    }
    payment = client.order.create(data=payment_data)
    context = {
        'payment': payment,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': payment_data['amount'],
        'currency': payment_data['currency'],
    }
    return render(request, 'premium.html', context)

@csrf_exempt
@login_required
def payment_handler(request):
    if request.method == 'POST':
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
            customer = request.user.customer  # No try-except here; assume login ensures Customer exists
            customer.access = "Premium"
            customer.save()
            return redirect('today_transactions')
        except razorpay.errors.SignatureVerificationError:
            return render(request, 'payment_failure.html')
        except Exception as e:
            return HttpResponseBadRequest(f"Error: {str(e)}")
    return HttpResponseBadRequest("Invalid request method")