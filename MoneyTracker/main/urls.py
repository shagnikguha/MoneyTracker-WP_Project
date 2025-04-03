from django.urls import path, include
from .views import auth_view, today_transactions_view, transaction_history_view

urlpatterns = [
    path('', auth_view, name='auth'),
    path('today_transactions', today_transactions_view, name='today_transactions'),
    path('transaction_history', transaction_history_view, name='transaction_history'),
]