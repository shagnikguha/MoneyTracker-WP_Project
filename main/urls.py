from django.urls import path
from .views import (
    login_view, register_view, today_transactions_view,
    transaction_history_view, index_view, edit_transaction_view,
    delete_transaction_view,
    # New payment views
    initiate_payment_view, payment_callback_view, payment_status_view,premium
)

urlpatterns = [
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('today_transactions', today_transactions_view, name='today_transactions'),
    path('transaction_history', transaction_history_view, name='transaction_history'),
    path('transaction/edit/<int:transaction_id>/', edit_transaction_view, name='edit_transaction'),
    path('transaction/delete/<int:transaction_id>/', delete_transaction_view, name='delete_transaction'),
    
    # PhonePe payment routes
    path('payment/initiate/', initiate_payment_view, name='initiate_payment'),
    path('payment/callback/', payment_callback_view, name='payment_callback'),
    path('payment/status/<str:transaction_id>/', payment_status_view, name='payment_status'),

    ##subscription path
    path('subscription/', premium, name='subscription'),
]