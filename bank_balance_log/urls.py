# bank_log/urls.py
from django.urls import path
from . import views

app_name = 'bank_log'

urlpatterns = [
    path('set-balance/', views.set_bank_balance_view, name='set_bank_balance'),
    path('add-transaction/', views.add_bank_transaction_view, name='add_bank_transaction'),
    # Main view for bank log, handles initial load and filtering
    path('', views.bank_log_main_view, name='bank_log_main'),
]
