from django.contrib import messages
from django.urls import reverse
from django.views import View


def get_message_list(request):
    return [{'text': msg.message, 'tags': msg.tags} for msg in messages.get_messages(request)]
    
class BaseTableView(View):
    """
    Base class to handle common table-related logic.
    Views can override `required_controls` to specify only the controls they need.
    """
    # Default table controls (All available options)
    TABLE_CONTROLS = [
        "search",
        "filterOption",
        "columnVisibility",
        "exportButton",
        "addButton", 
        "checkbox",
        "pageLimit",
        "pageInfo",
        "pageNavigation",
    ]
    DEFAULT_TABLE_CONTROLS = [
        "search",
        "columnVisibility",
        "exportButton",
        "pageLimit",
        "pageNavigation",
    ]

    # Views can override this to specify only required controls
    required_controls = None  # If None, all controls are used
    list_service_class = None
    list_url_name = None
    list_url_parameter = {}
    target = "hTableContainer"

    def __init__(self, **kwargs):
        """Ensure that list_service_class is defined in child classes."""
        super().__init__(**kwargs)
        if self.list_service_class is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'list_service_class'"
            )
        if self.list_url_name is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'list_url'")

    async def get_context_data(self, request, config_data, dynamic_params = None):
        """Fetch the list service context data asynchronously."""
        # config_data = {
        #     "query": request.GET.get("search", ""),
        #     "sort_by": request.GET.get("sort", ""),
        #     "page": int(request.GET.get("page", 1)),
        #     "page_limit": int(request.GET.get("limit", 10)),
        #     "requested_columns": request.GET.getlist("columns"),
        #     "sorting": request.GET.get("sorting", ""),
        # }
         # Update list_url_parameter dynamically

        if dynamic_params:
            self.list_url_parameter.update(dynamic_params)
            
        if self.list_url_parameter:
            list_url = reverse(self.list_url_name, kwargs=self.list_url_parameter)
        else:
            list_url = reverse(self.list_url_name)

        context = await self.list_service_class.get_list_data(config_data)

        context = {
            **context,
            "table_controls": self.get_table_controls(),
            "list_url": list_url,
            "target": self.target
        }
        return context

    def get_table_controls(self):
        """Returns the required controls or defaults to all controls."""
        return self.required_controls if self.required_controls is not None else self.DEFAULT_TABLE_CONTROLS
