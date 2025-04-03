from django.urls import path, include
from .views import (
    login_view, register_view, today_transactions_view,
    transaction_history_view, index_view, edit_transaction_view,
    delete_transaction_view
)

urlpatterns = [
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('today_transactions', today_transactions_view, name='today_transactions'),
    path('transaction_history', transaction_history_view, name='transaction_history'),
    path('transaction/edit/<int:transaction_id>/', edit_transaction_view, name='edit_transaction'),
    path('transaction/delete/<int:transaction_id>/', delete_transaction_view, name='delete_transaction'),
]