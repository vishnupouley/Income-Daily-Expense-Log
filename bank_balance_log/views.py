# bank_log/views.py
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods  # type: ignore
from pydantic import ValidationError
import json
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from schema.bank_balance_log.bank_balance_log_schema import (
    BankAccountCreateOrUpdate, BankTransactionCreateRequest,
    BankTransactionFilterInputSchema, BankTransactionSchema, BankLogContextData  # Updated schema
)
from bank_balance_log.services import BankLogService
from typing import Optional


# --- Helper Functions ---
def _parse_json_body(request: HttpRequest) -> Optional[dict]:
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
    return None


def _get_bank_filter_params_from_request(request_get_dict: dict) -> BankTransactionFilterInputSchema:
    today = timezone.now().date()
    
    # Safely handle integer conversions with defaults
    try:
        page = int(request_get_dict.get('page', '1')) if request_get_dict.get('page', '1') else 1
    except (ValueError, TypeError):
        page = 1
        
    try:
        page_size = int(request_get_dict.get('page_size', '10')) if request_get_dict.get('page_size', '10') else 10
    except (ValueError, TypeError):
        page_size = 10

    filter_data = {
        'filter_month_year': request_get_dict.get('filter_month_year', today.strftime('%Y-%m')),
        'filter_date': request_get_dict.get('filter_date'),
        'page': page,
        'page_size': page_size,
        'sort_by': request_get_dict.get('sort_by'),
        'transaction_type': request_get_dict.get('transaction_type')
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
        return BankTransactionFilterInputSchema.model_validate(filter_data)
    except ValidationError:
        return BankTransactionFilterInputSchema(
            filter_month_year=today.strftime('%Y-%m'),
            page=1,
            page_size=10
        )

# --- Main View & Balance Setting ---


@require_GET
async def bank_log_main_view(request: HttpRequest) -> HttpResponse:
    filters = _get_bank_filter_params_from_request(request.GET.dict())
    # Call the refactored service method
    context_data: BankLogContextData = await BankLogService.get_transactions_context_data(filters)
    print(context_data.model_dump())

    context = {
        'data': context_data.model_dump(),  # Contains pagination and all other data
        'add_button': {
            'name': 'Add Transaction',
            'url': reverse('bank_balance_log:add_transaction_form_row'),
            "target": "tbody#Htb_Htable",
            'swap': "beforeend"
        },
        'target': "Htable",
        'list_url': reverse('bank_balance_log:bank_log_main'),
        'columns': ['date_logged', 'transaction_type', 'amount', 'description', 'balance_after_transaction'],
        'menu_items': [
            {'name': 'Monthly Log', 'url': reverse(
                'monthly_log:monthly_log_main')},
            {'name': 'Bank Balance Log', 'url': reverse(
                'bank_balance_log:bank_log_main')}
        ],
    }

    template_name = 'cotton/components/table/index.html' if request.htmx else 'bank_balance_log/index.html'
    # Example for targeting only table body
    if request.htmx and request.headers.get("HX-Target") == "Htb_Htable":
        template_name = 'cotton/components/table/table_body.html'

    response = render(request, template_name, context)
    response.headers['HX-Trigger'] = f'{{"currentSortChanged": "{context_data.current_filters_applied.sort_by}"}}'
    return response


@require_POST
async def set_bank_balance_view(request: HttpRequest) -> HttpResponse:
    try:
        raw_data = _parse_json_body(
            request) if request.content_type == 'application/json' else request.POST.dict()
        if raw_data is None:
            return JsonResponse({'errors': "Invalid data format."}, status=400)
        balance_data = BankAccountCreateOrUpdate.model_validate(raw_data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors(include_input=False)}, status=400)
    except Exception as e:
        return JsonResponse({'errors': f"Invalid input: {str(e)}"}, status=400)

    await BankLogService.set_or_update_bank_balance(balance_data)

    filters = _get_bank_filter_params_from_request(request.GET.dict())
    context_data = await BankLogService.get_transactions_context_data(filters)
    context = {
        'log_data': context_data,
        'balance_update_success_message': "Bank balance updated successfully."
    }
    return render(request, 'cotton/components/table/table.html', context)


# --- HTMX Inline Bank Transaction Row Views ---

@require_GET
async def add_bank_transaction_form_row_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'bank_balance_log/partials/add_row.html', {})


@require_POST
async def save_new_bank_transaction_view(request: HttpRequest) -> HttpResponse:
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
        transaction_data_create = BankTransactionCreateRequest.model_validate(
            raw_data)
    except ValidationError as e:
        return JsonResponse({'errors': e.errors(include_input=False)}, status=400)
    except Exception as e:
        return JsonResponse({'errors': f"Invalid input: {str(e)}"}, status=400)

    try:
        new_transaction_obj = await BankLogService.record_transaction(transaction_data_create)
    except Exception as service_e:
        return JsonResponse({'errors': f"Failed to record transaction: {str(service_e)}"}, status=500)

    transaction_schema = BankTransactionSchema.model_validate(
        new_transaction_obj)
    context = {'row': transaction_schema}
    return render(request, 'bank_balance_log/partials/row.html', context)


@require_http_methods(["GET", "POST"])
async def cancel_add_bank_transaction_row_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse(status=200)
