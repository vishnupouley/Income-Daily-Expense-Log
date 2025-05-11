# monthly_income/models.py
from django.utils import timezone
from django.conf import settings
from django.db import models
from decimal import Decimal

class MonthlySalary(models.Model):
    """
    Stores the user's declared monthly salary for a specific month.
    """
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    # Stores the first day of the month for which this salary applies
    month_year = models.DateField() 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensures a user can only have one salary entry per month
        unique_together = ('month_year',)
        ordering = ['-month_year', '-updated_at']

    def __str__(self):
        return f"{self.month_year.strftime('%Y-%m')} - Salary: {self.salary_amount}"

class Expense(models.Model):
    """
    Stores individual expense records for a user.
    """
    # Optional link to a specific monthly salary record. 
    # Useful if you want to tie expenses directly to a declared salary for a month.
    # For simplicity in calculating running balances, we might primarily rely on the expense's date.
    monthly_salary_ref = models.ForeignKey(MonthlySalary, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date_logged = models.DateTimeField(default=timezone.now) # Changed from auto_now_add for more control if needed, but default to now.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_logged']

    def __str__(self):
        return f"{self.date_logged.strftime('%Y-%m-%d %H:%M')} - Amount: {self.amount} - {self.description}"

