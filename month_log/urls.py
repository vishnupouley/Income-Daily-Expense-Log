# monthly_log/urls.py
from django.urls import path
from . import views

app_name = 'monthly_log'

urlpatterns = [
    path('set-salary/', views.set_monthly_salary_view, name='set_salary'),
    path('add-expense/', views.add_expense_view, name='add_expense'),
    path('update-expense/<int:expense_id>/', views.update_expense_view, name='update_expense'),
    path('delete-expense/<int:expense_id>/', views.delete_expense_view, name='delete_expense'),
    path('', views.monthly_log_main_view, name='monthly_log_main'), 
]
