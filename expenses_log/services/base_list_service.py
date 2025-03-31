from django.utils.translation import gettext
from collections import defaultdict
from django.db.models import Q
from typing import List, Any
from django.apps import apps
from schema.list_schema import ListServiceConfig, ColumnInfo, ListServiceResponse, PaginationContext

class BaseListService:

    @staticmethod
    def default_exclude_columns():
        return ["created_at","modified_at","created_by","modified_by","is_valid"]

    @staticmethod
    async def get_all_columns(model: Any, config: ListServiceConfig) -> List[ColumnInfo]:
        
        all_columns = [
            {"name": field.name, "field_name":field.name, "verbose_name": gettext(str(field.verbose_name)) if field.verbose_name else field.name}
            for field in model._meta.fields
        ]

        # if hasattr(model, "get_full_name"):
        #     all_columns.append({
        #         "name": "full_name",
        #         "verbose_name": "Full Name"
        #     })

        if config.allowed_methods:
            custom_methods = [
                {
                    "name": method_name,
                    "field_name": model.get_ordering(method_name),
                    "verbose_name": gettext(method_name.replace("get_", "").replace("_", " ").title())
                }
                for method_name in config.allowed_methods  # 👈 Only include allowed methods
                if hasattr(model, method_name) and callable(getattr(model, method_name))
            ]

            # Combine both fields and custom methods
            custom_methods.extend(all_columns)
            all_columns = custom_methods
        
        filtered_columns = [
            ColumnInfo(
                name=col['name'],                  
                verbose_name=col['verbose_name'],  
                field_name=col['field_name'],  
                hidden=col['name'] in config.hidden_columns,
            )
            for col in all_columns
        ]
        return [col for col in filtered_columns if col.name not in config.exclude_columns]

    @staticmethod
    async def get_columns(all_columns: List[ColumnInfo], requested_columns: List[str], hidden_columns: List[str]) -> List[ColumnInfo]:
        
        if 'all' in requested_columns:
            return all_columns
        else:
            if requested_columns:

                return [col for col in all_columns if col.name in requested_columns or col.name in hidden_columns]
            
        return all_columns

    @staticmethod
    async def process_list_service(config: ListServiceConfig) -> ListServiceResponse:
        Model = apps.get_model(config.app, config.model)

        query_filter = Q()     
        for key, value in config.filter.items():
            if key.endswith("__ne"):  # Handle "not equal" condition
                actual_key = key[:-4]  # Remove "__ne" from key
                if isinstance(value, list):
                    query_filter &= ~Q(**{f"{actual_key}__in": value})  # Exclude multiple values
                else:
                    query_filter &= ~Q(**{actual_key: value})  # Exclude a single value
            elif isinstance(value, list):  # Handle lists using __in
                query_filter &= Q(**{f"{key}__in": value})
            else:
                query_filter &= Q(**{key: value})


        # Get columns
        all_columns = await BaseListService.get_all_columns(Model, config)
        columns = await BaseListService.get_columns(all_columns, config.requested_columns, config.hidden_columns)
        
        db_column_names = [col.name for col in columns if col.name in [f.name for f in Model._meta.fields]]
        computed_column_names = [col.name for col in columns if col.name not in db_column_names]
        
        # Build query using manager
        column_names = [col for col in db_column_names]
        
        # get the foreign key values 
        if config.foreign_keys:

            column_modified = []
            for column in column_names:
                if column in config.foreign_keys:
                    column_modified.append(config.foreign_keys[column])
                else:
                    column_modified.append(column)

            column_names = column_modified
        
        query_conditions = await Model.objects.build_query_conditions(config.query, column_names, query_filter)
        
        # Get count using manager
        total_items = await Model.objects.count_filtered(query_conditions)

        page_limit = total_items if config.page_limit == 0 else config.page_limit
        start_index = (config.page - 1) * page_limit
        end_index = start_index + page_limit

        # Handle sorting using manager
        sorting = config.sorting.split(",") if config.sorting else []        
        
        if 'get_' in config.sort_by:
            config.sort_by = Model.get_ordering(config.sort_by)

        if config.sort_by:
            sorting = await Model.objects.toggle_sorting(sorting, config.sort_by)
        
        # Get data using manager
        data = await Model.objects.get_paginated_data(
            query_conditions=query_conditions,
            columns=column_names,
            start_index=start_index,
            end_index=end_index,
            sorting=sorting if sorting else None,
            foreign_keys=config.foreign_keys
        )

        for row in data:
            instance = await Model.objects.aget(id=row["id"])  # Fetch instance to call methods
            for computed_column in computed_column_names:
                if hasattr(instance, computed_column):
                    row[computed_column] = getattr(instance, computed_column)()  # Call the method dynamically                    

        # Get pagination context using manager
        pagination_dict = await Model.objects.get_pagination_context(
            config.page, total_items, page_limit
        )
        pagination_context = PaginationContext(**pagination_dict)

        if 'all' in config.requested_columns:
            config.requested_columns = column_names
            config.requested_columns.append('all')

        priority_map = defaultdict(lambda: float('inf'), {name: index for index, name in enumerate(config.default_column)})
        # Sort the list based on the defined order
        sorted_columns = sorted(columns, key=lambda col: priority_map[col.name])

        # Print sorted result
        columns = sorted_columns

        return ListServiceResponse(
            data=data,
            search=config.query,
            columns=columns,
            all_columns=all_columns,
            pagination=pagination_context,
            hidden_columns=config.hidden_columns,
            requested_columns=config.requested_columns,
            sorting=",".join(sorting) if sorting else "",
        )
