from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
logger = logging.getLogger(__name__)

from .models import Transaction, Payment
from .forms import InputForm
from .phonepe_utils import create_payment_request, verify_payment_callback

from django.contrib import messages
from django.conf import settings

def index_view(request):
    return render(request, 'index.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
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
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}!")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

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
    data = Transaction.objects.filter(user=request.user).order_by('-date', '-id')
    return render(request, 'transaction_history.html', {'data': data})

@login_required
def edit_transaction_view(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        form = InputForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Transaction updated successfully!")
            # Redirect back to the page they came from
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('today_transactions')))
    else:
        form = InputForm(instance=transaction)
    
    return render(request, 'edit_transaction.html', {'form': form})

@login_required
def delete_transaction_view(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        # Redirect back to the page they came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('today_transactions')))
    
    return redirect('today_transactions')

# ----- New PhonePe Payment Views -----

@login_required
def initiate_payment_view(request):
    """View to initiate a PhonePe payment"""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        transaction_type = request.POST.get('transaction_type', 'Expense')
        category = request.POST.get('category', 'Other')
        date = request.POST.get('date', timezone.now().date().strftime('%Y-%m-%d'))
        description = request.POST.get('description', '')
        recurring = request.POST.get('recurring') == 'on'
        
        print(f"Initiating payment with amount={amount}, type={transaction_type}, category={category}, date={date}")
        
        if not amount:
            messages.error(request, "Amount is required.")
            return render(request, 'initiate_payment.html', {'today': timezone.now().date()})
        
        try:
            amount = float(amount)
            # Create payment request
            payment_data = create_payment_request(request, amount, request.user)
            
            if payment_data['success']:
                # Create a payment record
                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    payment_transaction_id=payment_data['transaction_id'],
                    status='pending'
                )
                print(f"Created payment with ID: {payment.id}, transaction_id: {payment_data['transaction_id']}")
                
                # Store transaction details in session
                pending_transaction = {
                    'transaction_type': transaction_type,
                    'category': category,
                    'date': date,  # Ensure date is serializable
                    'description': description,
                    'recurring': recurring,
                    'payment_id': payment_data['transaction_id']  # Link to payment transaction ID
                }
                
                request.session['pending_transaction'] = pending_transaction
                request.session.modified = True  # Mark the session as modified
                request.session.save()  # Explicitly save the session
                
                print(f"Stored in session: {pending_transaction}")
                print(f"Full session: {dict(request.session)}")
                
                # Redirect to PhonePe payment page
                return redirect(payment_data['payment_url'])
            else:
                print(f"Payment initialization failed: {payment_data.get('error')}")
                messages.error(request, f"Payment initialization failed: {payment_data.get('error')}")
        except ValueError:
            messages.error(request, "Invalid amount.")
    
    context = {'today': timezone.now().date()}
    return render(request, 'initiate_payment.html', context)

@csrf_exempt
def payment_callback_view(request):
    """Callback endpoint for PhonePe"""
    print("[CALLBACK] PhonePe callback received")
    
    if request.method == 'POST':
        # Get data from request
        try:
            request_data = json.loads(request.body) if request.body else {}
            print(f"[CALLBACK] Request data: {request_data}")
            
            # Verify the callback
            verification = verify_payment_callback(
                request_data, 
                settings.PHONEPAY_SALT_KEY, 
                settings.PHONEPAY_SALT_INDEX
            )
            
            if verification['success']:
                data = verification['data']
                merchant_transaction_id = data.get('merchantTransactionId')
                payment_status = data.get('code')
                print(f"[CALLBACK] Verified payment: {merchant_transaction_id}, status: {payment_status}")
                
                try:
                    # Find the payment by transaction ID
                    payment = Payment.objects.get(payment_transaction_id=merchant_transaction_id)
                    print(f"[CALLBACK] Found payment: {payment.id}")
                    
                    # Update the payment status
                    if payment_status == 'PAYMENT_SUCCESS':
                        payment.status = 'success'
                        payment.phonepe_transaction_id = data.get('transactionId')
                        payment.save()
                        print(f"[CALLBACK] Updated payment status to success")
                        
                        # Create a transaction here in the callback
                        if not payment.associated_transaction:
                            try:
                                # Create a transaction
                                transaction = Transaction.objects.create(
                                    user=payment.user,
                                    amount=payment.amount,
                                    transaction_type='Expense',
                                    category='Other',
                                    date=timezone.now().date(),
                                    description=f"PhonePe payment: {merchant_transaction_id}",
                                    recurring=False
                                )
                                print(f"[CALLBACK] Created transaction: {transaction.id}")
                                
                                # Link transaction to payment
                                payment.associated_transaction = transaction
                                payment.save()
                                print(f"[CALLBACK] Linked transaction to payment")
                            except Exception as e:
                                print(f"[CALLBACK] Error creating transaction: {str(e)}")
                                import traceback
                                traceback.print_exc()
                        
                        return JsonResponse({'status': 'success'})
                    else:
                        payment.status = 'failed'
                        payment.save()
                        print(f"[CALLBACK] Updated payment status to failed")
                        return JsonResponse({'status': 'failed'})
                
                except Payment.DoesNotExist:
                    print(f"[CALLBACK] Payment not found: {merchant_transaction_id}")
                    return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=400)
            
            print("[CALLBACK] Invalid callback data")
            return JsonResponse({'status': 'error', 'message': 'Invalid callback data'}, status=400)
        except Exception as e:
            print(f"[CALLBACK] Error processing callback: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return HttpResponse(status=405)  # Method not allowed


@csrf_exempt
def payment_status_view(request, transaction_id):
    """Handle payment status and create transaction"""
    print(f"[PAYMENT STATUS] View called for transaction: {transaction_id}")
    print(f"User authenticated: {request.user.is_authenticated}")
    
    try:
        # Find the payment by transaction_id, don't check user
        payment = Payment.objects.get(payment_transaction_id=transaction_id)
        print(f"[PAYMENT STATUS] Found payment record: {payment.id}, status: {payment.status}")
        
        # Get the user from the payment record
        user = payment.user
        print(f"[PAYMENT STATUS] Payment belongs to user: {user.username}")
        
        # Check if a transaction already exists
        if payment.associated_transaction:
            print(f"[PAYMENT STATUS] Transaction already exists: {payment.associated_transaction.id}")
            messages.info(request, "This payment has already been processed.")
            return redirect('today_transactions')
            
        # Update payment status if needed
        if payment.status == 'pending':
            payment.status = 'success'
            payment.save()
            print(f"[PAYMENT STATUS] Updated payment status to success")
        
        # Create transaction if payment successful
        if payment.status == 'success':
            # Default values for transaction
            transaction_type = 'Expense'
            category = 'Other'
            description = f"PhonePe payment {transaction_id}"
            recurring = False
            
            # Use current date
            date_obj = timezone.now().date()
            
            try:
                # Create transaction
                print(f"[PAYMENT STATUS] Creating transaction with: amount={payment.amount}, type={transaction_type}, category={category}")
                
                transaction = Transaction(
                    user=user,  # Use the user from the payment
                    amount=payment.amount,
                    transaction_type=transaction_type,
                    category=category,
                    date=date_obj,
                    description=description,
                    recurring=recurring
                )
                transaction.save()
                
                print(f"[PAYMENT STATUS] Created transaction with ID: {transaction.id}")
                
                # Associate with payment
                payment.associated_transaction = transaction
                payment.save()
                
                print(f"[PAYMENT STATUS] Associated transaction {transaction.id} with payment {payment.id}")
                
                messages.success(request, "Payment successful! Transaction has been added.")
                
                # Login the user if not authenticated
                if not request.user.is_authenticated:
                    from django.contrib.auth import login
                    login(request, user)
                    print(f"[PAYMENT STATUS] Logged in user: {user.username}")
                
                return redirect('today_transactions')
                
            except Exception as e:
                print(f"[PAYMENT STATUS] Error creating transaction: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Failed to create transaction: {str(e)}")
                return redirect('today_transactions')
        else:
            print(f"[PAYMENT STATUS] Payment not successful, status: {payment.status}")
            messages.error(request, "Payment was not successful.")
            return redirect('today_transactions')
            
    except Payment.DoesNotExist:
        print(f"[PAYMENT STATUS] Payment not found for transaction_id: {transaction_id}")
        messages.error(request, "Payment information not found.")
        return redirect('today_transactions')
        
    except Exception as e:
        print(f"[PAYMENT STATUS] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('today_transactions')