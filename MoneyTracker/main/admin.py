from django.contrib import admin
from .models import Customer, Transaction

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'access')  # show username, email, access
    list_filter  = ('access',)
    search_fields = ('user__username', 'user__email')  # allow searching by username or email

    def username(self, obj):
        return obj.user.username
    username.admin_order_field = 'user__username'
    username.short_description = 'Username'

    def email(self, obj):
        return obj.user.email
    email.admin_order_field = 'user__email'
    email.short_description = 'Email'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'date', 'category')
    list_filter  = ('transaction_type', 'category', 'date')
    search_fields = ('user__user__username',)  # if you want to search by Customer→User→username
