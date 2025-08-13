from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class MovementType(str, Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"

class ReferenceType(str, Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    INITIAL = "INITIAL"
    # Add empty string as a special case if needed
    EMPTY = ""

class StockMovementBase(BaseModel):
    item_id: int
    branch_id: int
    movement_type: MovementType
    quantity: int
    previous_stock: int
    new_stock: int
    reference_type: ReferenceType
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    created_by: int

class StockMovementCreate(StockMovementBase):
    pass

class StockMovementResponse(StockMovementBase):
    movement_id: int
    created_at: datetime
    item_name: Optional[str] = None
    branch_name: Optional[str] = None
    created_by_name: Optional[str] = None
    reference_type: Optional[ReferenceType] = None  # Made optional

    class Config:
        from_attributes = True
        json_encoders = {
            ReferenceType: lambda v: v.value if v else None
        }

class MovementFilter(BaseModel):
    item_id: Optional[int] = None
    branch_id: Optional[int] = None
    movement_type: Optional[MovementType] = None
    reference_type: Optional[ReferenceType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None