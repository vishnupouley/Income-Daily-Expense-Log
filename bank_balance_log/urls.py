# bank_balance_log/urls.py
from django.urls import path
from . import views

app_name = 'bank_balance_log'

urlpatterns = [
    # Main page and balance setting (not inline table)
    path('', views.bank_log_main_view, name='bank_log_main'),
    path('set-balance/', views.set_bank_balance_view, name='set_bank_balance'),

    # HTMX Inline Row Actions for Bank Transactions
    path('transaction/add-form/', views.add_bank_transaction_form_row_view, name='add_transaction_form_row'),
    path('transaction/save-new/', views.save_new_bank_transaction_view, name='save_new_transaction'),
    path('transaction/cancel-add/', views.cancel_add_bank_transaction_row_view, name='cancel_add_transaction_row'),
    
    # No edit/delete for bank transactions as per requirement
]
