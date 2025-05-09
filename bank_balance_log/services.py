# bank_log/services.py
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional
from django.contrib.auth import get_user_model
from django.db import transaction, F
from django.db.models import Count
from django.db.models.functions import TruncDate
from asgiref.sync import sync_to_async
from django.utils import timezone

from .models import BankAccount, BankTransaction
from schema.bank_balance_log.bank_balance_log_schema import (
    BankAccountCreateOrUpdate, BankAccountSchema,
    BankTransactionCreateRequest, BankTransactionSchema,
    BankDateFilterSchema, BankTransactionFilterInputSchema, BankLogViewData
)

User = get_user_model()

class BankLogService:

    @staticmethod
    @sync_to_async
    def set_or_update_bank_balance(user: User, balance_data: BankAccountCreateOrUpdate) -> BankAccountSchema:
        """
        Sets or updates the bank balance for the user.
        If the account doesn't exist, it's created.
        """
        account, created = BankAccount.objects.update_or_create(
            user=user,
            defaults={'current_balance': balance_data.initial_balance, 'last_updated': timezone.now()}
        )
        return BankAccountSchema.model_validate(account)

    @staticmethod
    @sync_to_async
    def get_bank_account_details(user: User) -> Optional[BankAccountSchema]:
        """
        Retrieves the bank account details for the user.
        """
        try:
            account = BankAccount.objects.get(user=user)
            return BankAccountSchema.model_validate(account)
        except BankAccount.DoesNotExist:
            return None

    @staticmethod
    async def record_transaction(user: User, transaction_data: BankTransactionCreateRequest) -> BankTransactionSchema:
        """
        Records a new bank transaction (debit or credit) and updates the account balance.
        This method is designed to be atomic.
        """
        # This function needs to be atomic to prevent race conditions on balance update.
        # We'll use sync_to_async to wrap the database operations within a transaction.
        
        @sync_to_async
        def _atomic_transaction_operation():
            with transaction.atomic():
                account, created = BankAccount.objects.get_or_create(user=user)

                new_balance = account.current_balance
                if transaction_data.transaction_type == BankTransaction.TransactionType.DEBIT:
                    new_balance -= transaction_data.amount
                elif transaction_data.transaction_type == BankTransaction.TransactionType.CREDIT:
                    new_balance += transaction_data.amount
                
                # Update account balance using F() expression for safety, though direct assignment within transaction is also safe.
                # BankAccount.objects.filter(pk=account.pk).update(current_balance=new_balance, last_updated=timezone.now())
                # account.refresh_from_db() # To get the updated values if using .update()

                account.current_balance = new_balance
                account.last_updated = timezone.now()
                account.save()


                transaction_date_logged = transaction_data.date_logged or timezone.now()
                
                bank_tx = BankTransaction.objects.create(
                    user=user,
                    account=account,
                    transaction_type=transaction_data.transaction_type,
                    amount=transaction_data.amount,
                    description=transaction_data.description,
                    balance_after_transaction=account.current_balance, # The balance *after* this tx
                    date_logged=transaction_date_logged
                )
                return BankTransactionSchema.model_validate(bank_tx)

        return await _atomic_transaction_operation()


    @staticmethod
    @sync_to_async
    def get_bank_log_view_data(user: User, filters: BankTransactionFilterInputSchema) -> BankLogViewData:
        """
        Retrieves bank transactions based on filters and current account balance.
        """
        account_details = None
        try:
            account = BankAccount.objects.get(user=user)
            account_details = BankAccountSchema.model_validate(account)
        except BankAccount.DoesNotExist:
            # If no account, no transactions or balance to show, but we can still return empty structure
            pass

        # Base queryset for transactions
        transaction_queryset = BankTransaction.objects.filter(user=user)

        # Apply date filtering
        if filters.filter_date:
            transaction_queryset = transaction_queryset.filter(date_logged__date=filters.filter_date)
        elif filters.filter_month_year:
            year, month = map(int, filters.filter_month_year.split('-'))
            transaction_queryset = transaction_queryset.filter(date_logged__year=year, date_logged__month=month)
        
        # Apply transaction type filtering
        if filters.transaction_type:
            transaction_queryset = transaction_queryset.filter(transaction_type=filters.transaction_type)

        # Apply sorting
        if filters.sort_by:
            transaction_queryset = transaction_queryset.order_by(filters.sort_by)
        else:
            transaction_queryset = transaction_queryset.order_by('-date_logged', '-created_at') # Default sort

        # Get total count for pagination before slicing
        total_transaction_count = transaction_queryset.count()

        # Apply pagination
        start_index = (filters.page - 1) * filters.page_size
        end_index = start_index + filters.page_size
        paginated_transactions_qs = transaction_queryset[start_index:end_index]

        processed_transactions = [BankTransactionSchema.model_validate(tx) for tx in paginated_transactions_qs]
        
        total_pages = (total_transaction_count + filters.page_size - 1) // filters.page_size if filters.page_size > 0 else 1
        if total_pages == 0 and total_transaction_count > 0 : total_pages = 1


        return BankLogViewData(
            bank_account=account_details,
            transactions=processed_transactions,
            total_transaction_count=total_transaction_count,
            date_filters=BankLogService._get_last_n_unique_transaction_dates(user, 10), # Call static method
            current_page=filters.page,
            total_pages=total_pages,
            page_size=filters.page_size
        )

    @staticmethod
    # This is a synchronous helper method
    def _get_last_n_unique_transaction_dates(user: User, count: int) -> List[BankDateFilterSchema]:
        """
        Retrieves the last N unique dates on which bank transactions were logged.
        """
        unique_dates_qs = BankTransaction.objects.filter(user=user)\
            .annotate(transaction_date=TruncDate('date_logged'))\
            .values('transaction_date')\
            .distinct()\
            .order_by('-transaction_date')[:count]

        date_filters = []
        for idx, item in enumerate(unique_dates_qs):
            log_date = item['transaction_date']
            if log_date:
                date_filters.append(BankDateFilterSchema(
                    id=idx + 1,
                    date_value=log_date.strftime('%Y-%m-%d'),
                    display_text=log_date.strftime('%b %d, %Y')
                ))
        return date_filters
