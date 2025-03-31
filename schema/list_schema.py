from pydantic import BaseModel, Field
from typing import Dict, List, Any

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

class PaginationContext(BaseModel):
    per_page_options: List[int] = [5, 10, 25, 50, 100]
    current_page: int
    total_pages: int
    page_range: List[int]
    has_previous: bool
    has_next: bool
    previous_page: int
    next_page: int
    total_items: int
    start_item: int
    end_item: int
    per_page: int

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
    pagination: PaginationContext
    hidden_columns: List[str]
    requested_columns: List[str]
    sorting: str

