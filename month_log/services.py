# month_log/services.py
from decimal import Decimal
from datetime import date
from typing import List, Tuple, Optional
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.functions import TruncDate
from asgiref.sync import sync_to_async
from django.utils import timezone
import math  # For math.ceil

from .models import MonthlySalary, Expense
from schema.month_log.month_log_schema import (
    MonthlySalaryCreate, MonthlySalarySchema,
    ExpenseCreate, ExpenseUpdate, ExpenseSchema, DateFilterSchema,
    ExpenseFilterInputSchema, MonthlyLogContextData  # Updated schema
)
from schema.list_schema import PaginationDetails
from bank_balance_log.services import BankLogService
from schema.bank_balance_log.bank_balance_log_schema import BankTransactionCreateRequest

User = get_user_model()


class MonthlyIncomeService:

    @staticmethod
    @sync_to_async
    def get_expense_by_id(expense_id: int) -> Optional[Expense]:
        try:
            return Expense.objects.get(pk=expense_id)
        except Expense.DoesNotExist:
            return None

    @staticmethod
    @sync_to_async
    def set_or_update_monthly_salary(salary_data: MonthlySalaryCreate) -> MonthlySalarySchema:
        target_month_year = date(
            salary_data.month_year.year, salary_data.month_year.month, 1)
        salary_obj, created = MonthlySalary.objects.update_or_create(
            month_year=target_month_year,
            defaults={'salary_amount': salary_data.salary_amount}
        )
        return MonthlySalarySchema.model_validate(salary_obj)

    @staticmethod
    @sync_to_async
    def get_monthly_salary(target_date: date) -> Optional[MonthlySalarySchema]:
        month_start = date(target_date.year, target_date.month, 1)
        try:
            salary_obj = MonthlySalary.objects.get(
                month_year=month_start)
            return MonthlySalarySchema.model_validate(salary_obj)
        except MonthlySalary.DoesNotExist:
            return None

    @staticmethod
    async def add_expense(expense_data: ExpenseCreate) -> Tuple[Optional[Expense], Optional[str]]:
        expense_date_logged = expense_data.date_logged or timezone.now()
        new_expense_obj = None
        try:
            @sync_to_async
            def _create_expense_atomically():
                return Expense.objects.create(
                    amount=expense_data.amount,
                    description=expense_data.description, date_logged=expense_date_logged
                )
            new_expense_obj = await _create_expense_atomically()
            bank_transaction_data = BankTransactionCreateRequest(
                transaction_type="DEBIT", amount=new_expense_obj.amount,
                description=f"Monthly Expense: {new_expense_obj.description}",
                date_logged=new_expense_obj.date_logged
            )
            await BankLogService.record_transaction(transaction_data=bank_transaction_data)
            return new_expense_obj, None
        except Exception as e:
            if new_expense_obj and new_expense_obj.pk:
                await sync_to_async(new_expense_obj.delete)()
                return None, f"Bank transaction failed: {str(e)}. Expense creation was rolled back."
            return None, f"Failed to add expense or log bank transaction: {str(e)}"

    @staticmethod
    async def update_expense(expense_id: int, expense_data: ExpenseUpdate) -> Tuple[Optional[Expense], Optional[str]]:
        try:
            expense_obj = await sync_to_async(Expense.objects.get)(pk=expense_id)
            updated_fields = expense_data.model_dump(exclude_unset=True)
            if not updated_fields:
                return expense_obj, "No update data provided."
            original_amount = expense_obj.amount
            original_date = expense_obj.date_logged
            for field, value in updated_fields.items():
                setattr(expense_obj, field, value)
            await sync_to_async(expense_obj.save)()
            warning_message = ""
            if "amount" in updated_fields and updated_fields["amount"] != original_amount:
                warning_message += " Expense amount changed; please review bank log."
            if "date_logged" in updated_fields and updated_fields["date_logged"] != original_date:
                warning_message += " Expense date changed; please review bank log."
            return expense_obj, warning_message if warning_message else "Expense updated successfully."
        except Expense.DoesNotExist:
            return None, "Expense not found."
        except Exception as e:
            return None, f"Error updating expense: {str(e)}"

    @staticmethod
    async def delete_expense(expense_id: int) -> Tuple[bool, Optional[str]]:
        try:
            expense_obj = await sync_to_async(Expense.objects.get)(pk=expense_id)
            comp_amount, comp_desc = expense_obj.amount, expense_obj.description
            await sync_to_async(expense_obj.delete)()
            bank_tx_data = BankTransactionCreateRequest(
                transaction_type="CREDIT", amount=comp_amount,
                description=f"Reversal for deleted expense: {comp_desc}", date_logged=timezone.now()
            )
            try:
                await BankLogService.record_transaction(transaction_data=bank_tx_data)
                return True, "Expense deleted and bank credit logged."
            except Exception as bank_e:
                return True, f"Expense deleted, but failed to log bank credit: {str(bank_e)}."
        except Expense.DoesNotExist:
            return False, "Expense not found."
        except Exception as e:
            return False, f"Error deleting expense: {str(e)}"

    @staticmethod
    @sync_to_async
    def get_expenses_context_data(params: ExpenseFilterInputSchema) -> MonthlyLogContextData:
        today = timezone.now().date()

        # Determine target month for salary and overall period summary
        target_period_date = today
        if params.filter_date:
            target_period_date = params.filter_date
        elif params.filter_month_year:
            year, month = map(int, params.filter_month_year.split('-'))
            target_period_date = date(year, month, 1)  # Use first of month

        target_month_for_salary = date(
            target_period_date.year, target_period_date.month, 1)

        current_salary_schema: Optional[MonthlySalarySchema] = None
        salary_amount_for_month = Decimal('0.00')
        try:
            salary_obj = MonthlySalary.objects.get(
                month_year=target_month_for_salary)
            current_salary_schema = MonthlySalarySchema.model_validate(
                salary_obj)
            salary_amount_for_month = salary_obj.salary_amount
        except MonthlySalary.DoesNotExist:
            pass

        # Base queryset
        expense_queryset = Expense.objects.all()

        # Apply date filtering for the list of expenses
        if params.filter_date:
            expense_queryset = expense_queryset.filter(
                date_logged__date=params.filter_date)
        elif params.filter_month_year:
            year, month = map(int, params.filter_month_year.split('-'))
            expense_queryset = expense_queryset.filter(
                date_logged__year=year, date_logged__month=month)
        else:  # Default to current month if no specific filter
            expense_queryset = expense_queryset.filter(
                date_logged__year=today.year, date_logged__month=today.month)

        # Apply sorting
        if params.sort_by:
            expense_queryset = expense_queryset.order_by(params.sort_by)
        else:
            expense_queryset = expense_queryset.order_by('-date_logged')

        # Pagination
        total_items = expense_queryset.count()
        total_pages = math.ceil(
            total_items / params.page_size) if params.page_size > 0 else 0
        if total_pages == 0 and total_items > 0:
            total_pages = 1  # Ensure at least one page if items exist

        current_page = params.page
        if current_page > total_pages and total_pages > 0:
            current_page = total_pages  # Cap current page
        if current_page < 1:
            current_page = 1

        start_item_index = (current_page - 1) * params.page_size
        end_item_index = start_item_index + params.page_size
        paginated_expenses_qs = expense_queryset[start_item_index:end_item_index]

        # Calculate summary for the *entire* filtered period (month or day) for display
        # This queryset is for the summary figures like "total spent"
        summary_period_queryset = Expense.objects.all()
        if params.filter_date:  # Summary for specific day
            summary_period_queryset = summary_period_queryset.filter(
                date_logged__date=params.filter_date)
        else:  # Summary for the month (either current or specified by filter_month_year)
            summary_period_queryset = summary_period_queryset.filter(
                date_logged__year=target_month_for_salary.year,
                date_logged__month=target_month_for_salary.month
            )

        total_spent_for_period_dict = summary_period_queryset.aggregate(
            total_spent=Sum('amount'))
        total_spent_for_period = total_spent_for_period_dict['total_spent'] or Decimal(
            '0.00')

        saved_amount_for_period = Decimal('0.00')
        # "Saved amount" makes most sense when viewing a full month against a monthly salary
        if not params.filter_date:
            saved_amount_for_period = salary_amount_for_month - total_spent_for_period

        # Process paginated expenses to add running balance within their month
        processed_expenses_schemas: List[ExpenseSchema] = []
        # To calculate running balance, we need all expenses in the *month of each expense*, up to that expense.
        # This is complex if paginated expenses span multiple months (not typical for this app's design).
        # Assuming expenses are filtered by a single month or day.

        # Fetch all expenses for the month of the target_period_date for balance calculation
        all_expenses_for_balance_month_qs = Expense.objects.filter(
            date_logged__year=target_month_for_salary.year,  # Use salary month as reference
            date_logged__month=target_month_for_salary.month
        ).order_by('date_logged', 'created_at')

        running_balance_map: dict[int, Decimal] = {}
        current_running_spent_for_balance_calc = Decimal('0.00')
        for exp_for_bal in all_expenses_for_balance_month_qs:
            current_running_spent_for_balance_calc += exp_for_bal.amount
            running_balance_map[exp_for_bal.id] = salary_amount_for_month - \
                current_running_spent_for_balance_calc

        for expense_obj in paginated_expenses_qs:
            schema_obj = ExpenseSchema.model_validate(expense_obj)
            # Get balance from the map; this assumes expense_obj is within the target_month_for_salary
            if expense_obj.date_logged.year == target_month_for_salary.year and \
               expense_obj.date_logged.month == target_month_for_salary.month:
                schema_obj.balance_after_this_expense_in_month = running_balance_map.get(
                    expense_obj.id)
            else:  # Should not happen if filters are by month/day
                schema_obj.balance_after_this_expense_in_month = None
            processed_expenses_schemas.append(schema_obj)

        pagination_details = PaginationDetails(
            current_page=current_page,
            page_size=params.page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next_page=current_page < total_pages,
            has_previous_page=current_page > 1,
            next_page_number=current_page + 1 if current_page < total_pages else None,
            previous_page_number=current_page - 1 if current_page > 1 else None,
            start_item_index=start_item_index if total_items > 0 else None,
            # -1 because end_item_index is exclusive for slicing
            end_item_index=end_item_index - 1 if total_items > 0 else None,
            display_start_item=start_item_index + 1 if total_items > 0 else 0,
            display_end_item=min(
                end_item_index, total_items) if total_items > 0 else 0,
            page_range=[5, 10, 15, 20, 25]
        )

        return MonthlyLogContextData(
            current_salary=current_salary_schema,
            total_spent_for_period=total_spent_for_period,
            saved_amount_for_period=saved_amount_for_period,
            expenses=processed_expenses_schemas,
            date_filters=MonthlyIncomeService._get_last_n_unique_expense_dates_sync(
                10),
            pagination=pagination_details,
            current_filters_applied=params
        )

    @sync_to_async
    @staticmethod
    def get_sum_for_balance(exp_obj, user_obj):
        return Expense.objects.filter(
            user=user_obj, date_logged__year=exp_obj.date_logged.year,
            date_logged__month=exp_obj.date_logged.month, date_logged__lte=exp_obj.date_logged
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    @sync_to_async
    @staticmethod
    def get_sum(exp_obj, user_obj):
        return Expense.objects.filter(
            user=user_obj,
            date_logged__year=exp_obj.date_logged.year,
            date_logged__month=exp_obj.date_logged.month,
            date_logged__lte=exp_obj.date_logged
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    @staticmethod
    def _get_last_n_unique_expense_dates_sync(count: int) -> List[DateFilterSchema]:
        # ... (no changes to this helper method)
        unique_dates_qs = Expense.objects.all()\
            .annotate(expense_date=TruncDate('date_logged'))\
            .values('expense_date')\
            .distinct()\
            .order_by('-expense_date')[:count]
        date_filters = []
        for idx, item in enumerate(unique_dates_qs):
            log_date = item['expense_date']
            if log_date:
                date_filters.append(DateFilterSchema(
                    id=idx + 1, date_value=log_date.strftime('%Y-%m-%d'),
                    display_text=log_date.strftime('%b %d, %Y')
                ))
        return date_filters
