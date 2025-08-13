from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from typing import Optional
from enum import Enum

# Enums for fixed values
class TransferStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MovementType(str, Enum):
    RECEIVING = "RECEIVING"
    DISPATCH = "DISPATCH"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"
    LOSS = "LOSS"

# Pydantic Models
class TransferRequestSearchResult(BaseModel):
    transfer_id: int
    transfer_number: str
    status: str
    priority: str
    from_branch: str
    to_branch: str
    requested_by: str
    request_date: datetime

    class Config:
        orm_mode = True

class StockMovementSearchResult(BaseModel):
    movement_id: int
    item_id: int
    item_name: str
    branch_id: int
    branch_name: str
    movement_type: str
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: int
    created_by_name: str
    created_at: datetime

    class Config:
        orm_mode = True
