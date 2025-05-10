# monthly_log/urls.py
from django.urls import path
from . import views

app_name = 'monthly_log'

urlpatterns = [
    # Main page and salary setting (not inline table)
    path('', views.monthly_log_main_view, name='monthly_log_main'),
    path('set-salary/', views.set_monthly_salary_view, name='set_salary'),

    # HTMX Inline Row Actions for Expenses
    path('expense/add-form/', views.add_expense_form_row_view, name='add_expense_form_row'),
    path('expense/save-new/', views.save_new_expense_view, name='save_new_expense'),
    path('expense/cancel-add/', views.cancel_add_expense_row_view, name='cancel_add_expense_row'),
    
    path('expense/edit-form/<int:expense_id>/', views.edit_expense_form_row_view, name='edit_expense_form_row'),
    path('expense/save-edited/<int:expense_id>/', views.save_edited_expense_view, name='save_edited_expense'),
    path('expense/cancel-edit/<int:expense_id>/', views.cancel_edit_expense_row_view, name='cancel_edit_expense_row'),
    
    path('expense/delete/<int:expense_id>/', views.delete_expense_view, name='delete_expense'),
]
