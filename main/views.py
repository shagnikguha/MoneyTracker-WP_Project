from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
import requests
logger = logging.getLogger(__name__)

from .models import Transaction, Payment,Subscribed
from .forms import InputForm
from .phonepe_utils import create_payment_request, verify_payment_callback

from django.contrib import messages
from django.conf import settings

import json
import pandas as pd
from collections import defaultdict

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

# ----- New Logout View -----
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')

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

# ----- New History View for added graphs -----
@login_required
def transaction_history_view(request):
    data = Transaction.objects.filter(user=request.user).order_by('-date', '-id')

    monthly_avg_expense = {}
    income_vs_expense = {"labels": [], "income": [], "expense": []}
    
    if data.exists():
        
        # transactions by month and type
        monthly_grouped = defaultdict(lambda: {'Expense': 0, 'Income': 0, 'Expense_count': 0, 'Income_count': 0})
        
        for transaction in data:
            month_year = transaction.date.strftime('%Y-%m')
            transaction_type = transaction.transaction_type
            amount = float(transaction.amount)
            
            monthly_grouped[month_year][transaction_type] += amount
            monthly_grouped[month_year][f'{transaction_type}_count'] += 1
        
        sorted_months = sorted(monthly_grouped.keys())

        # Calculate monthly average expenses
        sorted_avg_expense = {}
        for month in sorted_months:
            values = monthly_grouped[month]
            if values['Expense_count'] > 0:
                sorted_avg_expense[month] = values['Expense'] / values['Expense_count']
        
        monthly_avg_expense = sorted_avg_expense
        # income vs expense data
        sorted_months = sorted(monthly_grouped.keys())
        income_vs_expense = {
            'labels': sorted_months,
            'income': [monthly_grouped[month]['Income'] for month in sorted_months],
            'expense': [monthly_grouped[month]['Expense'] for month in sorted_months]
        }
    
    # Convert to JSON
    monthly_avg_expense_json = json.dumps(monthly_avg_expense)
    income_vs_expense_json = json.dumps(income_vs_expense)
    
    return render(request, 'transaction_history.html', {'data': data, 'monthly_avg_expense': monthly_avg_expense_json, 'income_vs_expense': income_vs_expense_json})


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
    logger.info("[CALLBACK] PhonePe callback received")
    
    if request.method == 'POST':
        try:
            request_data = json.loads(request.body) if request.body else {}
            logger.info(f"[CALLBACK] Request data: {request_data}")
            
            verification = verify_payment_callback(
                request_data, 
                settings.PHONEPAY_SALT_KEY, 
                settings.PHONEPAY_SALT_INDEX
            )
            
            if verification['success']:
                data = verification['data']
                merchant_transaction_id = data.get('merchantTransactionId')
                payment_status = data.get('code')
                logger.info(f"[CALLBACK] Verified payment: {merchant_transaction_id}, status: {payment_status}")
                
                try:
                    payment = Payment.objects.get(payment_transaction_id=merchant_transaction_id)
                    logger.info(f"[CALLBACK] Found payment: {payment.id}")
                    
                    if payment_status == 'PAYMENT_SUCCESS':
                        payment.status = 'success'
                        payment.phonepe_transaction_id = data.get('transactionId')
                        payment.save()
                        logger.info(f"[CALLBACK] Updated payment status to success")
                    else:
                        payment.status = 'failed'
                        payment.save()
                        logger.info(f"[CALLBACK] Updated payment status to failed")
                    
                    return JsonResponse({'status': 'success'})
                
                except Payment.DoesNotExist:
                    logger.error(f"[CALLBACK] Payment not found: {merchant_transaction_id}")
                    return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=400)
            
            logger.error("[CALLBACK] Invalid callback data")
            return JsonResponse({'status': 'error', 'message': 'Invalid callback data'}, status=400)
        except Exception as e:
            logger.error(f"[CALLBACK] Error processing callback: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return HttpResponse(status=405)

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
    
def is_subscribed(user):   ##a function to check if subscribed or not
    """Check if user has active subscription"""
    try:
        subscription = Subscribed.objects.get(user=user)
        return subscription.status
    except Subscribed.DoesNotExist:
        return False

@login_required
def premium(request):
    subscription_active = is_subscribed(request.user)
    return render(request, 'premium.html', {'subscription_active': subscription_active})

@login_required
def chatbot(request):
    """View for the chatbot page, only accessible to premium subscribers"""
    subscription_active = is_subscribed(request.user)
    return render(request, 'chatbot.html', {'subscription_active': subscription_active})

@login_required
@require_POST
def chatbot_query(request):
    """API endpoint for processing chatbot queries using Gemini"""
    # Check if user is subscribed
    if not is_subscribed(request.user):
        return HttpResponseBadRequest("Premium subscription required")
        
    try:
        # Parse the request body
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        query = body.get('query', '')
        
        if not query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        # Your Gemini API key should be stored in environment variables or settings
        # For this example, we'll assume it's in Django settings
        from django.conf import settings
        
        # Call the Gemini API
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not gemini_api_key:
            return JsonResponse({'error': 'API key not configured'}, status=500)
            
        # Set up the API endpoint
        gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
        
        # Construct the prompt to focus on finance and economics topics
        instruction = (
            "You are a financial assistant chatbot that only answers questions related to money, "
            "finance, economics, budgeting, investing, and related topics. "
            "If the user asks about something unrelated to these topics, politely explain that "
            "you can only help with financial matters. "
            "Be concise, accurate, and helpful with finance-related questions."
        )
        
        prompt = f"{instruction}\n\nUser question: {query}"
        
        # Make the API request
        response = requests.post(
            f"{gemini_endpoint}?key={gemini_api_key}",
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 800
                }
            }
        )
        
        # Process the response
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract the text from the response
            generated_text = ""
            try:
                candidates = response_data.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts:
                        generated_text = parts[0].get('text', '')
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing Gemini response: {str(e)}")
                return JsonResponse({'error': 'Error parsing API response'}, status=500)
                
            return JsonResponse({'response': generated_text})
        else:
            logger.error(f"Gemini API error: {response.status_code} - {response.text}")
            return JsonResponse({'error': f'API error: {response.status_code}'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def initiate_subscription_payment(request):
    """View to initiate a PhonePe subscription payment"""
    if request.method == 'POST':
        amount = 200  # Fixed amount for subscription
        
        try:
            # Generate transaction ID first to use in both redirect URL and payment request
            from .phonepe_utils import generate_transaction_id
            transaction_id = generate_transaction_id()
            
            # Create custom redirect URL for subscription
            from django.urls import reverse
            redirect_url = request.build_absolute_uri(
                reverse('subscription_status', args=[transaction_id])
            )
            
            # Modified create_payment_request call with custom redirect URL
            from .phonepe_utils import create_payment_request
            payment_data = create_payment_request(
                request, 
                amount, 
                request.user,
                transaction_id=transaction_id,  # Pass the pre-generated transaction ID
                redirect_url=redirect_url  # Pass the custom redirect URL
            )
            
            if payment_data['success']:
                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    payment_transaction_id=payment_data['transaction_id'],
                    status='pending'
                )
                logger.info(f"Created subscription payment with ID: {payment.id}, transaction_id: {payment_data['transaction_id']}")
                
                # Store subscription info in session
                request.session['pending_subscription'] = {
                    'payment_id': payment_data['transaction_id'],
                    'is_subscription': True  # Explicitly mark as subscription
                }
                request.session.modified = True
                request.session.save()
                
                logger.info(f"Stored in session: {request.session['pending_subscription']}")
                return redirect(payment_data['payment_url'])
            else:
                logger.error(f"Subscription payment initialization failed: {payment_data.get('error')}")
                messages.error(request, f"Payment initialization failed: {payment_data.get('error')}")
        except Exception as e:
            logger.error(f"Error initiating subscription payment: {str(e)}", exc_info=True)
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('premium')


##view for subscription status
@csrf_exempt  # Add this to prevent CSRF issues with external redirects
def subscription_status_view(request, transaction_id):
    """Handle subscription payment status"""
    logger.info(f"[SUBSCRIPTION STATUS] View called for transaction: {transaction_id}")
    
    try:
        # Find payment by transaction ID without requiring user authentication
        payment = Payment.objects.get(payment_transaction_id=transaction_id)
        user = payment.user
        
        # Authenticate user if needed
        if not request.user.is_authenticated:
            login(request, user)
            logger.info(f"[SUBSCRIPTION STATUS] Logged in user: {user.username}")
        
        # Rest of your existing code...

        
        # Update payment status if still pending
        if payment.status == 'pending':
            payment.status = 'success'
            payment.save()
            logger.info(f"[SUBSCRIPTION STATUS] Updated payment status to success")
        
        # Handle subscription if payment is successful
        if payment.status == 'success':
            try:
                # First check if subscription exists
                try:
                    subscription = Subscribed.objects.get(user=request.user)
                    subscription.status = True
                    subscription.save()
                    logger.info(f"[SUBSCRIPTION STATUS] Updated existing subscription for user: {request.user.username}")
                except Subscribed.DoesNotExist:
                    # Create new subscription if it doesn't exist
                    subscription = Subscribed.objects.create(user=request.user, status=True)
                    logger.info(f"[SUBSCRIPTION STATUS] Created new subscription for user: {request.user.username}")
                
                messages.success(request, "Subscription activated successfully!")
                
                # Clear session data
                if 'pending_subscription' in request.session:
                    del request.session['pending_subscription']
                    request.session.modified = True
                    request.session.save()
            
            except Exception as e:
                logger.error(f"[SUBSCRIPTION STATUS] Error updating subscription: {str(e)}", exc_info=True)
                messages.error(request, f"Failed to activate subscription: {str(e)}")
        else:
            logger.warning(f"[SUBSCRIPTION STATUS] Payment not successful, status: {payment.status}")
            messages.error(request, "Subscription payment was not successful.")
        
    except Payment.DoesNotExist:
        logger.error(f"[SUBSCRIPTION STATUS] Payment not found for transaction_id: {transaction_id}")
        messages.error(request, "Payment information not found.")
    except Exception as e:
        logger.error(f"[SUBSCRIPTION STATUS] Unexpected error: {str(e)}", exc_info=True)
        messages.error(request, f"An unexpected error occurred: {str(e)}")
    
    return redirect('premium')
