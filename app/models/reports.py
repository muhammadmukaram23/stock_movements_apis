from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from typing import Optional

class StockSummaryResponse(BaseModel):
    branch_name: str
    total_items: Optional[int] = 0  # Make optional with default
    total_stock: Optional[int] = 0
    total_reserved: Optional[int] = 0
    total_available: Optional[int] = 0
    low_stock_items: Optional[int] = 0
    out_of_stock_items: Optional[int] = 0

    class Config:
        orm_mode = True

class StockValuationResponse(BaseModel):
    branch_name: str
    item_name: str
    current_stock: int
    unit_price: float
    total_value: float

class StockAgingResponse(BaseModel):
    item_name: str
    branch_name: str
    current_stock: int
    last_movement: datetime
    days_since_movement: int

class TransferSummaryResponse(BaseModel):
    request_date: date
    total_requests: int
    pending: int
    approved: int
    completed: int
    rejected: int

class MostRequestedItemsResponse(BaseModel):
    item_name: str
    request_count: int
    total_requested: int

class TransferPerformanceResponse(BaseModel):
    from_branch: str
    to_branch: str
    total_transfers: int
    avg_approval_days: float
    avg_dispatch_days: float
    avg_delivery_days: float
    avg_total_days: float

class UserActivityResponse(BaseModel):
    full_name: str
    branch_name: str
    role_name: str
    transfer_requests: int
    dispatches: int
    receipts: int
    stock_movements: int

class SystemLogResponse(BaseModel):
    log_id: int
    user_id: Optional[int]
    user_name: Optional[str]
    action: str
    details: str
    created_at: datetime