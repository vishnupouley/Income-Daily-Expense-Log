# bank_log/services.py
from datetime import date 
from typing import List, Optional
from django.contrib.auth import get_user_model # type: ignore
from django.db import transaction 
from django.db.models.functions import TruncDate # type: ignore
from asgiref.sync import sync_to_async # type: ignore
from django.utils import timezone
import math # For math.ceil

from .models import BankAccount, BankTransaction
from schema.bank_balance_log.bank_balance_log_schema import (
    BankAccountCreateOrUpdate, BankAccountSchema,
    BankTransactionCreateRequest, BankTransactionSchema,
    BankDateFilterSchema, BankTransactionFilterInputSchema, 
    BankLogContextData, PaginationDetails # Updated Schemas
)
from schema.list_schema import PaginationDetails

User = get_user_model()

class BankLogService:

    @staticmethod
    @sync_to_async
    def get_bank_transaction_by_id(transaction_id: int) -> Optional[BankTransaction]:
        try:
            return BankTransaction.objects.get(pk=transaction_id)
        except BankTransaction.DoesNotExist:
            return None

    @staticmethod
    @sync_to_async
    def set_or_update_bank_balance(balance_data: BankAccountCreateOrUpdate) -> BankAccountSchema:
        account, created = BankAccount.objects.update_or_create(
            defaults={'current_balance': balance_data.initial_balance, 'last_updated': timezone.now()}
        )
        return BankAccountSchema.model_validate(account)

    @staticmethod
    @sync_to_async
    def get_bank_account_details() -> Optional[BankAccountSchema]:
        try:
            account = BankAccount.objects.get()
            return BankAccountSchema.model_validate(account)
        except BankAccount.DoesNotExist:
            return None

    @staticmethod
    async def record_transaction(user: User, transaction_data: BankTransactionCreateRequest) -> BankTransaction:
        @sync_to_async
        def _atomic_transaction_operation() -> BankTransaction:
            with transaction.atomic():
                account, created = BankAccount.objects.get_or_create(user=user)
                new_balance = account.current_balance
                if transaction_data.transaction_type == BankTransaction.TransactionType.DEBIT:
                    new_balance -= transaction_data.amount
                else: new_balance += transaction_data.amount
                account.current_balance = new_balance
                account.last_updated = timezone.now()
                account.save() 
                bank_tx = BankTransaction.objects.create(
                    user=user, account=account,
                    transaction_type=transaction_data.transaction_type,
                    amount=transaction_data.amount, 
                    description=transaction_data.description,
                    balance_after_transaction=account.current_balance, 
                    date_logged=transaction_data.date_logged or timezone.now()
                )
                return bank_tx
        return await _atomic_transaction_operation()

    @staticmethod
    @sync_to_async
    def get_transactions_context_data(params: BankTransactionFilterInputSchema) -> BankLogContextData:
        account_details_schema: Optional[BankAccountSchema] = None
        try:
            account = BankAccount.objects.get()
            account_details_schema = BankAccountSchema.model_validate(account)
        except BankAccount.DoesNotExist:
            pass 

        # Base queryset
        transaction_queryset = BankTransaction.objects.all()

        # Apply filters
        if params.filter_date:
            transaction_queryset = transaction_queryset.filter(date_logged__date=params.filter_date)
        elif params.filter_month_year:
            year, month = map(int, params.filter_month_year.split('-'))
            transaction_queryset = transaction_queryset.filter(date_logged__year=year, date_logged__month=month)
        
        if params.transaction_type:
            transaction_queryset = transaction_queryset.filter(transaction_type=params.transaction_type)

        # Apply sorting
        if params.sort_by:
            transaction_queryset = transaction_queryset.order_by(params.sort_by)
        else:
            transaction_queryset = transaction_queryset.order_by('-date_logged', '-created_at') 

        # Pagination
        total_items = transaction_queryset.count()
        total_pages = math.ceil(total_items / params.page_size) if params.page_size > 0 else 0
        if total_pages == 0 and total_items > 0: total_pages = 1

        current_page = params.page
        if current_page > total_pages and total_pages > 0 : current_page = total_pages
        if current_page < 1: current_page = 1

        start_item_index = (current_page - 1) * params.page_size
        end_item_index = start_item_index + params.page_size
        paginated_transactions_qs = transaction_queryset[start_item_index:end_item_index]

        processed_transaction_schemas = [BankTransactionSchema.model_validate(tx) for tx in paginated_transactions_qs]
        
        pagination_details = PaginationDetails(
            current_page=current_page,
            page_size=params.page_size,
            total_items=total_items,
            total_pages=total_pages,
            page_range=list(range(1, total_pages + 1)),
            has_next_page=current_page < total_pages,
            has_previous_page=current_page > 1,
            next_page_number=current_page + 1 if current_page < total_pages else None,
            previous_page_number=current_page - 1 if current_page > 1 else None,
            start_item_index=start_item_index if total_items > 0 else None,
            end_item_index=end_item_index -1 if total_items > 0 else None,
            display_start_item=start_item_index + 1 if total_items > 0 else 0,
            display_end_item=min(end_item_index, total_items) if total_items > 0 else 0,
            per_page_options=[5, 10, 15, 20, 25]
        )

        return BankLogContextData(
            bank_account=account_details_schema,
            transactions=processed_transaction_schemas,
            date_filters=BankLogService._get_last_n_unique_transaction_dates_sync(10),
            pagination=pagination_details,
            current_filters_applied=params,
        )

    @staticmethod
    def _get_last_n_unique_transaction_dates_sync(count: int) -> List[BankDateFilterSchema]:
        # ... (no changes to this helper method)
        unique_dates_qs = BankTransaction.objects.all()\
            .annotate(transaction_date=TruncDate('date_logged'))\
            .values('transaction_date')\
            .distinct()\
            .order_by('-transaction_date')[:count]
        date_filters = []
        for idx, item in enumerate(unique_dates_qs):
            log_date = item['transaction_date']
            if log_date:
                date_filters.append(BankDateFilterSchema(
                    id=idx + 1, date_value=log_date.strftime('%Y-%m-%d'),
                    display_text=log_date.strftime('%b %d, %Y')
                ))
        return date_filters
