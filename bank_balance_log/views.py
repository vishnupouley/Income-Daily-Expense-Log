# bank_log/views.py
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from pydantic import ValidationError
import json
from datetime import date, datetime

from schema.bank_balance_log.bank_balance_log_schema import (
    BankAccountCreateOrUpdate, BankTransactionCreateRequest, 
    BankTransactionFilterInputSchema
)
from .services import BankLogService
from django.template.loader import render_to_string # For HTMX partials

# Helper to parse JSON body
def _parse_json_body(request: HttpRequest):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
    return None

@login_required
@require_POST
async def set_bank_balance_view(request: HttpRequest) -> HttpResponse:
    """
    Sets or updates the bank balance for the logged-in user.
    Expects form data or JSON.
    """
    try:
        if request.content_type == 'application/json':
            data = _parse_json_body(request)
            if data is None: return HttpResponseBadRequest("Invalid JSON data.")
        else: # Form data
            data = request.POST.dict()
            # Pydantic will handle Decimal conversion for initial_balance
        
        balance_data = BankAccountCreateOrUpdate.model_validate(data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors()}, status=400) # Or HTML error partial
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid input: {str(e)}")

    account_schema = await BankLogService.set_or_update_bank_balance(request.user, balance_data)
    
    # For HTMX, render a partial for the balance display
    # Simulating an HTMX response by re-fetching summary data
    today = date.today()
    filter_data = BankTransactionFilterInputSchema() # Default filters
    log_data = await BankLogService.get_bank_log_view_data(request.user, filter_data)

    html_response = render_to_string('bank_log/partials/bank_summary_partial.html', {
        'log_data': log_data, 
        'user': request.user,
        'success_message': f"Bank balance updated to {account_schema.current_balance}."
    })
    return HttpResponse(html_response)


@login_required
@require_POST
async def add_bank_transaction_view(request: HttpRequest) -> HttpResponse:
    """
    Adds a new bank transaction (debit/credit) for the logged-in user.
    Expects form data or JSON.
    """
    try:
        if request.content_type == 'application/json':
            data = _parse_json_body(request)
            if data is None: return HttpResponseBadRequest("Invalid JSON data.")
        else: # Form data
            data = request.POST.dict()
            # Pydantic handles Decimal for amount and Literal for transaction_type
            if 'date_logged' in data and data['date_logged']:
                 try:
                    data['date_logged'] = datetime.fromisoformat(data['date_logged'].replace('Z', '+00:00'))
                 except ValueError:
                    pass # Pydantic will try to parse

        transaction_data = BankTransactionCreateRequest.model_validate(data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors()}, status=400) # Or HTML error partial
    except Exception as e:
        return HttpResponseBadRequest(f"Invalid input: {str(e)}")


    try:
        transaction_schema = await BankLogService.record_transaction(request.user, transaction_data)
    except Exception as e: # Catch errors from service layer (e.g., DB issues)
        # Log the error e
        return JsonResponse({'error': f"Failed to record transaction: {str(e)}"}, status=500)


    # For HTMX, trigger refresh of the transaction list and balance
    # Defaulting to a standard view after adding a transaction.
    filter_params = {
        'filter_month_year': request.GET.get('filter_month_year'),
        'filter_date': request.GET.get('filter_date'),
        'page': request.GET.get('page', '1'),
        'page_size': request.GET.get('page_size', '10'),
        'sort_by': request.GET.get('sort_by'),
        'transaction_type': request.GET.get('transaction_type')
    }
    if filter_params['filter_date']:
        filter_params.pop('filter_month_year', None)
        try:
            filter_params['filter_date'] = datetime.strptime(filter_params['filter_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            filter_params['filter_date'] = None
    
    try:
        filters = BankTransactionFilterInputSchema.model_validate(filter_params)
    except ValidationError: # Default if params are bad
        filters = BankTransactionFilterInputSchema()


    log_data = await BankLogService.get_bank_log_view_data(request.user, filters)
    
    html_response = render_to_string('bank_log/partials/transaction_list_and_summary_partial.html', {
        'log_data': log_data, 
        'user': request.user,
        'success_message': f"{transaction_schema.transaction_type.capitalize()} of {transaction_schema.amount} for '{transaction_schema.description}' recorded."
    })
    return HttpResponse(html_response)


@login_required
@require_GET
async def bank_log_main_view(request: HttpRequest) -> HttpResponse:
    """
    Displays the main bank log page, including transactions, balance, and filters.
    Handles filtering based on GET parameters.
    """
    try:
        raw_filter_params = request.GET.dict()
        if 'filter_date' in raw_filter_params and raw_filter_params['filter_date']:
            try:
                raw_filter_params['filter_date'] = datetime.strptime(raw_filter_params['filter_date'], '%Y-%m-%d').date()
            except ValueError:
                raw_filter_params.pop('filter_date', None)
        
        filters = BankTransactionFilterInputSchema.model_validate(raw_filter_params)
    except ValidationError as e:
        filters = BankTransactionFilterInputSchema() # Default filters
        # context_errors = e.errors()

    log_data = await BankLogService.get_bank_log_view_data(request.user, filters)
    
    context = {
        'log_data': log_data,
        'current_filters': filters.model_dump(),
        'user': request.user,
        # 'validation_errors': context_errors if 'context_errors' in locals() else None
    }

    if request.htmx:
        # If HTMX request (e.g., filtering), return only the partial
        return render(request, 'bank_log/partials/transaction_list_and_summary_partial.html', context)
    
    # Full page load
    return render(request, 'bank_log/bank_log_page.html', context)
