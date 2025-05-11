# bank_log/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal

class BankAccount(models.Model):
    """
    Represents a user's bank account. For simplicity, one account per user.
    """
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.current_balance}"

class BankTransaction(models.Model):
    """
    Stores individual bank transactions (debit or credit).
    """
    class TransactionType(models.TextChoices):
        DEBIT = 'DEBIT', 'Debit'
        CREDIT = 'CREDIT', 'Credit'

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=6, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    # Stores the balance of the account *after* this transaction was processed.
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    date_logged = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_logged', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} for {self.date_logged.strftime('%Y-%m-%d')}"
