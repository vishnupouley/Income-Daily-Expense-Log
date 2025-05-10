# monthly_income/views.py
from django.views.decorators.http import require_POST, require_GET, require_http_methods  # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required  # type: ignore
from asgiref.sync import sync_to_async  # For balance calculation in row views
from pydantic import ValidationError
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum  # For balance calculation in row views
from datetime import datetime
from decimal import Decimal  # For balance calculation in row views
import json

from schema.month_log.month_log_schema import (
    MonthlySalaryCreate, ExpenseCreate, ExpenseUpdate,
    ExpenseFilterInputSchema, ExpenseSchema, MonthlyLogContextData  # Updated schema
)
from month_log.services import MonthlyIncomeService
from typing import Optional


# --- Helper Functions ---
def _parse_json_body(request: HttpRequest) -> Optional[dict]:
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
    return None


def _get_filter_params_from_request(request_get_dict: dict) -> ExpenseFilterInputSchema:
    today = timezone.now().date()
    filter_data = {
        'filter_month_year': request_get_dict.get('filter_month_year', today.strftime('%Y-%m')),
        'filter_date': request_get_dict.get('filter_date'),
        'page': int(request_get_dict.get('page', '1')),
        'page_size': int(request_get_dict.get('page_size', '10')),
        'sort_by': request_get_dict.get('sort_by')
    }
    if filter_data.get('filter_date'):
        try:
            if isinstance(filter_data['filter_date'], str):
                filter_data['filter_date'] = datetime.strptime(
                    filter_data['filter_date'], '%Y-%m-%d').date()
            if filter_data['filter_date']:
                filter_data['filter_month_year'] = None
        except (ValueError, TypeError):
            filter_data['filter_date'] = None
            filter_data['filter_month_year'] = today.strftime('%Y-%m')
    try:
        return ExpenseFilterInputSchema.model_validate(filter_data)
    except ValidationError:
        return ExpenseFilterInputSchema(filter_month_year=today.strftime('%Y-%m'), page=1, page_size=10)

# --- Main View & Salary ---


@login_required
@require_GET
async def monthly_log_main_view(request: HttpRequest) -> HttpResponse:
    filters = _get_filter_params_from_request(request.GET.dict())
    # Call the refactored service method
    context_data: MonthlyLogContextData = await MonthlyIncomeService.get_expenses_context_data(request.user, filters)

    context = {
        'log_data': context_data,  # This now contains pagination and all other data
        'user': request.user,
        # current_filters_applied is already in context_data.pagination
    }
    # Determine template based on HTMX headers (user will handle this)
    # For now, assuming table.html for HTMX and index.html for full load
    template_name = 'cotton/components/table/index.html' if request.htmx else 'month_log/index.html'
    # Example for targeting only table body
    if request.htmx and request.GET.get("target_body"):
        template_name = 'cotton/components/table/table_body.html'

    return render(request, template_name, context)


@login_required
@require_POST
async def set_monthly_salary_view(request: HttpRequest) -> HttpResponse:
    try:
        raw_data = _parse_json_body(
            request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None:
            return JsonResponse({'errors': "Invalid data format."}, status=400)
        if 'month_year' in raw_data and isinstance(raw_data['month_year'], str):
            try:
                raw_data['month_year'] = datetime.strptime(
                    raw_data['month_year'], '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'errors': "Invalid date format."}, status=400)
        salary_data = MonthlySalaryCreate.model_validate(raw_data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors(include_input=False)}, status=400)
    except Exception as e:
        return JsonResponse({'errors': f"Invalid input: {str(e)}"}, status=400)

    await MonthlyIncomeService.set_or_update_monthly_salary(request.user, salary_data)

    # Re-fetch full context to update summary and potentially the table
    filters = _get_filter_params_from_request(request.GET.dict())
    context_data = await MonthlyIncomeService.get_expenses_context_data(request.user, filters)
    context = {
        'log_data': context_data, 'user': request.user,
        'salary_update_success_message': "Salary updated successfully."  # Example message
    }
    # Render the main table partial which includes the summary
    return render(request, 'cotton/components/table/table.html', context)


# --- HTMX Inline Expense Row Views (largely same, but ensure context for row.html is correct) ---

@login_required
@require_GET
async def add_expense_form_row_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'month_log/partials/add_row.html', {})


@login_required
@require_POST
async def save_new_expense_view(request: HttpRequest) -> HttpResponse:
    try:
        raw_data = _parse_json_body(
            request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None:
            return JsonResponse({'errors': "Invalid data format."}, status=400)
        if 'date_logged' in raw_data and isinstance(raw_data.get('date_logged'), str) and raw_data.get('date_logged'):
            try:
                raw_data['date_logged'] = datetime.fromisoformat(
                    raw_data['date_logged'].replace('Z', '+00:00'))
            except ValueError:
                pass
        else:
            raw_data.pop('date_logged', None)
        expense_data_create = ExpenseCreate.model_validate(raw_data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors(include_input=False)}, status=400)
    except Exception as e:
        return JsonResponse({'errors': f"Invalid input: {str(e)}"}, status=400)

    new_expense_obj, error_message = await MonthlyIncomeService.add_expense(request.user, expense_data_create)
    if error_message or not new_expense_obj:
        return JsonResponse({'errors': error_message or "Failed to save expense."}, status=400)

    expense_schema = ExpenseSchema.model_validate(new_expense_obj)
    # Calculate balance for this specific row
    salary_for_month_obj = await MonthlyIncomeService.get_monthly_salary(request.user, new_expense_obj.date_logged.date())
    salary_amount = salary_for_month_obj.salary_amount if salary_for_month_obj else Decimal(
        '0.00')

    total_spent_up_to = await MonthlyIncomeService.get_sum_for_balance(new_expense_obj, request.user)
    expense_schema.balance_after_this_expense_in_month = salary_amount - total_spent_up_to

    context = {'row': expense_schema, 'user': request.user}
    return render(request, 'month_log/partials/row.html', context)


@login_required
@require_http_methods(["GET", "POST"])
async def cancel_add_expense_row_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse(status=200)


@login_required
@require_GET
async def edit_expense_form_row_view(request: HttpRequest, expense_id: int) -> HttpResponse:
    expense = await MonthlyIncomeService.get_expense_by_id(request.user, expense_id)
    if not expense:
        return JsonResponse({'errors': "Expense not found."}, status=404)
    expense_schema = ExpenseSchema.model_validate(expense)
    context = {'row': expense_schema, 'user': request.user}
    return render(request, 'month_log/partials/edit_row.html', context)


@login_required
@require_POST
async def save_edited_expense_view(request: HttpRequest, expense_id: int) -> HttpResponse:
    expense_to_edit = await MonthlyIncomeService.get_expense_by_id(request.user, expense_id)
    if not expense_to_edit:
        return JsonResponse({'errors': "Expense not found."}, status=404)
    try:
        raw_data = _parse_json_body(
            request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None:
            return JsonResponse({'errors': "Invalid data format."}, status=400)
        if 'date_logged' in raw_data and isinstance(raw_data.get('date_logged'), str) and raw_data.get('date_logged'):
            try:
                raw_data['date_logged'] = datetime.fromisoformat(
                    raw_data['date_logged'].replace('Z', '+00:00'))
            except ValueError:
                pass
        expense_update_data = ExpenseUpdate.model_validate(raw_data)
        if not expense_update_data.model_dump(exclude_unset=True):
            original_schema = ExpenseSchema.model_validate(expense_to_edit)
            # Recalculate balance for original row display
            salary_obj = await MonthlyIncomeService.get_monthly_salary(request.user, original_schema.date_logged.date())
            salary_amt = salary_obj.salary_amount if salary_obj else Decimal(
                '0.00')

            
            total_s = await MonthlyIncomeService.get_sum(expense_to_edit, request.user)
            original_schema.balance_after_this_expense_in_month = salary_amt - total_s
            return render(request, 'month_log/partials/row.html', {'row': original_schema, 'user': request.user})
    except ValidationError as e:
        return JsonResponse({'errors': e.errors(include_input=False)}, status=400)
    except Exception as e:
        return JsonResponse({'errors': f"Invalid input: {str(e)}"}, status=400)

    updated_obj, message = await MonthlyIncomeService.update_expense(request.user, expense_id, expense_update_data)
    if not updated_obj:
        return JsonResponse({'errors': message or "Update failed."}, status=400)

    updated_schema = ExpenseSchema.model_validate(updated_obj)
    # Recalculate balance for updated row display
    salary_obj = await MonthlyIncomeService.get_monthly_salary(request.user, updated_schema.date_logged.date())
    salary_amt = salary_obj.salary_amount if salary_obj else Decimal('0.00')


    total_s = await MonthlyIncomeService.get_sum(updated_obj, request.user)
    updated_schema.balance_after_this_expense_in_month = salary_amt - total_s

    context = {'row': updated_schema, 'user': request.user}
    response = render(request, 'month_log/partials/row.html', context)
    if message and ("amount changed" in message or "date changed" in message):
        response['HX-Trigger'] = json.dumps(
            {'showInfoModal': {'message': message}})
    return response


@login_required
@require_http_methods(["GET", "POST"])
async def cancel_edit_expense_row_view(request: HttpRequest, expense_id: int) -> HttpResponse:
    expense = await MonthlyIncomeService.get_expense_by_id(request.user, expense_id)
    if not expense:
        return HttpResponse(status=404)

    expense_schema = ExpenseSchema.model_validate(expense)
    # Recalculate balance for row display
    salary_obj = await MonthlyIncomeService.get_monthly_salary(request.user, expense_schema.date_logged.date())
    salary_amt = salary_obj.salary_amount if salary_obj else Decimal('0.00')


    total_s = await MonthlyIncomeService.get_sum(expense, request.user)
    expense_schema.balance_after_this_expense_in_month = salary_amt - total_s

    context = {'row': expense_schema, 'user': request.user}
    return render(request, 'month_log/partials/row.html', context)


@login_required
@require_http_methods(["POST", "DELETE"])
async def delete_expense_view(request: HttpRequest, expense_id: int) -> HttpResponse:
    success, message = await MonthlyIncomeService.delete_expense(request.user, expense_id)
    if not success:
        return JsonResponse({'errors': message or "Delete failed."}, status=400)
    response = HttpResponse(status=200)
    if message and "bank transaction" in message:
        response['HX-Trigger'] = json.dumps(
            {'showInfoModal': {'message': message}})
    return response
