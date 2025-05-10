from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class ListServiceConfig(BaseModel):
    app: str
    model: str
    query: str = ""
    filter: Dict[str, Any] = Field(default_factory=dict)
    sort_by: str = ""
    page: int = 1
    page_limit: int = 10
    requested_columns: List[str] = Field(default_factory=list)
    exclude_columns: List[str] = Field(default_factory=list)
    hidden_columns: List[str]
    allowed_methods: List[str] = []
    default_column: List[str] = []
    sorting: str = ""
    foreign_keys: Dict[str, str] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

# --- Pagination Detail Schema (reusable) ---


class PaginationDetails(BaseModel):
    current_page: int
    page_size: int  # Renamed from per_page for consistency with input schema
    total_items: int  # Renamed from total_data
    total_pages: int
    has_next_page: bool
    has_previous_page: bool
    next_page_number: Optional[int] = None
    previous_page_number: Optional[int] = None
    start_item_index: Optional[int] = None  # 0-based index for slicing
    end_item_index: Optional[int] = None   # 0-based index for slicing
    display_start_item: Optional[int] = None  # 1-based for display
    display_end_item: Optional[int] = None   # 1-based for display
    page_range: Optional[List[int]] = [5, 10, 15, 20, 25]


class ColumnInfo(BaseModel):
    name: str
    verbose_name: str
    field_name: str
    hidden: bool


class ListServiceResponse(BaseModel):
    data: List[Dict]
    search: str
    columns: List[ColumnInfo]
    all_columns: List[ColumnInfo]
    pagination: PaginationDetails
    hidden_columns: List[str]
    requested_columns: List[str]
    sorting: str
