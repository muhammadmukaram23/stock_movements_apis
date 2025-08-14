from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Common base models
class TimeRange(BaseModel):
    start_date: date = Field(..., description="Start date for the report")
    end_date: date = Field(..., description="End date for the report")

class BranchItemPair(BaseModel):
    branch_id: int = Field(..., gt=0)
    item_id: int = Field(..., gt=0)

# Reporting Models
class MonthlyStockMovement(BaseModel):
    year: int
    month: int
    movement_type: str
    movement_count: int
    total_quantity: int

class BranchPerformance(BaseModel):
    branch_name: str
    transfers_sent: int
    transfers_received: int
    avg_fulfillment_days: Optional[float] = None
    rejections_sent: int

class ItemDemand(BaseModel):
    item_name: str
    item_code: str
    times_requested: int
    total_requested: int
    avg_requested_per_transfer: float
    requesting_branches: int

class SeasonalDemand(BaseModel):
    item_name: str
    month: int
    requests: int
    total_quantity: int

class StockTurnover(BaseModel):
    item_name: str
    branch_name: str
    current_stock: int
    total_outgoing: int
    turnover_ratio: float

# Notification Models
class ReorderAlert(BaseModel):
    item_name: str
    item_code: str
    branch_name: str
    available_stock: int
    minimum_stock_level: int
    reorder_quantity: int

class OverdueTransfer(BaseModel):
    transfer_number: str
    from_branch: str
    to_branch: str
    request_date: datetime
    expected_delivery_date: date
    days_overdue: int

class PendingApproval(BaseModel):
    transfer_number: str
    requesting_branch: str
    requested_by: str
    request_date: datetime
    priority: str
    hours_pending: int

class InactiveUser(BaseModel):
    full_name: str
    username: str
    branch_name: str
    last_login: Optional[datetime] = None
    days_since_login: int

# Data Validation Models
class NegativeStock(BaseModel):
    item_name: str
    branch_name: str
    current_stock: int

class StockMismatch(BaseModel):
    item_name: str
    branch_name: str
    movement_new_stock: int
    inventory_current_stock: int

# Maintenance Models
class TableSize(BaseModel):
    table_name: str
    row_count: int