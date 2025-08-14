

from pydantic import BaseModel,Field,field_validator

from typing import Optional, List
from datetime import date, datetime
from typing import Optional
from enum import Enum

class BulkMinStockUpdate(BaseModel):
    category_id: int = Field(..., gt=0, description="ID of the category to update")
    minimum_stock_level: int = Field(..., ge=0, description="New minimum stock level")

class BulkPriceUpdate(BaseModel):
    category_id: int = Field(..., gt=0, description="ID of the category to update")
    percentage_change: float = Field(..., description="Percentage change (positive or negative)")

class BulkTransferApproval(BaseModel):
    from_branch_id: int = Field(..., gt=0, description="Branch ID to approve transfers from")
    approved_by: int = Field(..., gt=0, description="User ID approving the transfers")

class BulkStockAdjustment(BaseModel):
    item_id: int = Field(..., gt=0, description="Item ID to adjust")
    branch_id: int = Field(..., gt=0, description="Branch ID where adjustment occurs")
    new_stock_level: int = Field(..., ge=0, description="New physical stock count")
    created_by: int = Field(..., gt=0, description="User ID performing the adjustment")

class BatchResponse(BaseModel):
    message: str
    affected_rows: int
    updated_data: Optional[List[dict]] = None

class StockAdjustmentResponse(BatchResponse):
    movement_id: Optional[int] = None
    previous_stock: Optional[int] = None
    new_stock: Optional[int] = None