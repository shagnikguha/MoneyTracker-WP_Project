from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    index_view,
    login_view,
    register_view,
    today_transactions_view,
    transaction_history_view,
    edit_transaction_view,
    delete_transaction_view,
    premium
)

urlpatterns = [
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # ← new logout
    path('register/', register_view, name='register'),
    path('today_transactions/', today_transactions_view, name='today_transactions'),
    path('transaction_history/', transaction_history_view, name='transaction_history'),
    path('transaction/edit/<int:transaction_id>/', edit_transaction_view, name='edit_transaction'),
    path('transaction/delete/<int:transaction_id>/', delete_transaction_view, name='delete_transaction'),
    path('subscription/', premium, name='subscription'),
]
