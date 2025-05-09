# monthly_income/views.py
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from pydantic import ValidationError
import json
from datetime import date, datetime
from typing import Any, Optional

from schema.month_log.month_log_schema import MonthlySalaryCreate, ExpenseCreate, ExpenseUpdate, ExpenseFilterInputSchema
from services import MonthlyIncomeService
from django.template.loader import render_to_string 

def _parse_json_body(request: HttpRequest) -> Optional[dict]:
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
    return None

def _get_common_view_filters(request_get_dict: dict) -> ExpenseFilterInputSchema:
    """Helper to parse filter parameters for refreshing views."""
    today = date.today()
    current_month_str = today.strftime('%Y-%m')
    
    filter_params = {
        'filter_month_year': request_get_dict.get('filter_month_year', current_month_str),
        'filter_date': request_get_dict.get('filter_date'),
        'page': request_get_dict.get('page', '1'),
        'page_size': request_get_dict.get('page_size', '10'),
        'sort_by': request_get_dict.get('sort_by')
    }
    if filter_params['filter_date']: 
        filter_params.pop('filter_month_year', None)
        try:
            filter_params['filter_date'] = datetime.strptime(filter_params['filter_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            filter_params['filter_date'] = None
            filter_params['filter_month_year'] = current_month_str # Fallback if date is bad

    try:
        return ExpenseFilterInputSchema.model_validate(filter_params)
    except ValidationError: 
        return ExpenseFilterInputSchema(filter_month_year=current_month_str)


async def _render_expense_list_and_summary(request: HttpRequest, user: Any, success_message: Optional[str] = None, error_message: Optional[str] = None) -> HttpResponse:
    """Helper to re-render the expense list and summary partial."""
    filters = _get_common_view_filters(request.GET.dict())
    log_data = await MonthlyIncomeService.get_monthly_log_data(user, filters)
    
    context = {
        'log_data': log_data, 
        'user': user,
        'current_filters': filters.model_dump(),
    }
    if success_message:
        context['success_message'] = success_message
    if error_message:
        context['error_message'] = error_message
        
    html_response = render_to_string('monthly_income/partials/expense_list_and_summary_partial.html', context)
    return HttpResponse(html_response)


@login_required
@require_POST
async def set_monthly_salary_view(request: HttpRequest) -> HttpResponse:
    try:
        raw_data = _parse_json_body(request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None: return HttpResponseBadRequest("Invalid data.")
        
        # Ensure month_year is parsed to date if it's a string
        if 'month_year' in raw_data and isinstance(raw_data['month_year'], str):
            try:
                raw_data['month_year'] = datetime.strptime(raw_data['month_year'], '%Y-%m-%d').date()
            except ValueError:
                return HttpResponseBadRequest("Invalid date format for month_year. Use YYYY-MM-DD.")

        salary_data = MonthlySalaryCreate.model_validate(raw_data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors()}, status=400)
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid input: {str(e)}")

    salary_schema = await MonthlyIncomeService.set_or_update_monthly_salary(request.user, salary_data)
    
    # For HTMX, re-render the summary part
    filters = _get_common_view_filters(request.GET.dict()) # Get current filters if any
    log_data = await MonthlyIncomeService.get_monthly_log_data(request.user, filters)
    
    html_response = render_to_string('monthly_income/partials/monthly_summary_partial.html', {
        'log_data': log_data, 
        'user': request.user,
        'success_message': f"Salary for {salary_schema.month_year.strftime('%B %Y')} set to {salary_schema.salary_amount}."
    })
    return HttpResponse(html_response)


@login_required
@require_POST
async def add_expense_view(request: HttpRequest) -> HttpResponse:
    try:
        raw_data = _parse_json_body(request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None: return HttpResponseBadRequest("Invalid data.")
        
        if 'date_logged' in raw_data and isinstance(raw_data.get('date_logged'), str) and raw_data.get('date_logged'):
             try:
                # Handle ISO format with or without Z
                raw_data['date_logged'] = datetime.fromisoformat(raw_data['date_logged'].replace('Z', '+00:00'))
             except ValueError:
                pass # Pydantic will try further parsing or use default

        expense_data = ExpenseCreate.model_validate(raw_data)
    except ValidationError as e:
        # For HTMX, could return an error message in a partial
        error_html = render_to_string('monthly_income/partials/form_errors_partial.html', {'errors': e.errors()})
        return HttpResponse(error_html, status=400)
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid input: {str(e)}")

    expense_schema, error_message = await MonthlyIncomeService.add_expense(request.user, expense_data)

    if error_message or not expense_schema:
        return await _render_expense_list_and_summary(request, request.user, error_message=error_message or "Failed to add expense.")
    
    success_msg = f"Expense '{expense_schema.description}' of {expense_schema.amount} added."
    return await _render_expense_list_and_summary(request, request.user, success_message=success_msg)


@login_required
@require_http_methods(["POST"]) # Typically updates are POST or PUT
async def update_expense_view(request: HttpRequest, expense_id: int) -> HttpResponse:
    try:
        raw_data = _parse_json_body(request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None: return HttpResponseBadRequest("Invalid data.")

        if 'date_logged' in raw_data and isinstance(raw_data.get('date_logged'), str) and raw_data.get('date_logged'):
             try:
                raw_data['date_logged'] = datetime.fromisoformat(raw_data['date_logged'].replace('Z', '+00:00'))
             except ValueError:
                pass
        
        update_data = ExpenseUpdate.model_validate(raw_data)
        if not update_data.model_dump(exclude_unset=True): # Check if any actual data was sent for update
             return await _render_expense_list_and_summary(request, request.user, error_message="No update information provided.")

    except ValidationError as e:
        error_html = render_to_string('monthly_income/partials/form_errors_partial.html', {'errors': e.errors()})
        return HttpResponse(error_html, status=400)
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid input for update: {str(e)}")

    expense_schema, message = await MonthlyIncomeService.update_expense(request.user, expense_id, update_data)

    if not expense_schema:
        return await _render_expense_list_and_summary(request, request.user, error_message=message or "Failed to update expense.")

    return await _render_expense_list_and_summary(request, request.user, success_message=message or "Expense updated.")


@login_required
@require_http_methods(["POST", "DELETE"]) # DELETE for semantic, POST if form used
async def delete_expense_view(request: HttpRequest, expense_id: int) -> HttpResponse:
    # For HTMX, a POST request from a form might be used to signify deletion as well.
    # True DELETE method is also supported.
    
    success, message = await MonthlyIncomeService.delete_expense(request.user, expense_id)

    if not success:
        return await _render_expense_list_and_summary(request, request.user, error_message=message or "Failed to delete expense.")

    # On successful deletion via HTMX, you might want to return an empty response if the row is removed client-side,
    # or re-render the list. Here we re-render.
    # If request.method == "DELETE" and request.htmx, can return HttpResponse(status=200) if row removed by hx-target swapping outerHTML of row to nothing.
    return await _render_expense_list_and_summary(request, request.user, success_message=message)


@login_required
@require_GET
async def monthly_log_main_view(request: HttpRequest) -> HttpResponse:
    filters = _get_common_view_filters(request.GET.dict())
    log_data = await MonthlyIncomeService.get_monthly_log_data(request.user, filters)
    
    context = {
        'log_data': log_data,
        'current_filters': filters.model_dump(), 
        'user': request.user,
    }

    if request.htmx:
        return render(request, 'monthly_income/partials/expense_list_and_summary_partial.html', context)
    
    return render(request, 'monthly_income/monthly_log_page.html', context)

