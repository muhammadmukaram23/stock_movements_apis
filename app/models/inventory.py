from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class StockStatus(str, Enum):
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOW_STOCK = "LOW_STOCK"
    NORMAL = "NORMAL"

class InventoryBase(BaseModel):
    item_id: int
    branch_id: int
    current_stock: Optional[int] = 0
    reserved_stock: Optional[int] = 0

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    reserved_stock: Optional[int] = None

# Response models
class BranchStockResponse(BaseModel):
    item_id: int
    item_name: str
    item_code: str
    category_name: str
    current_stock: int
    reserved_stock: int
    available_stock: int
    minimum_stock_level: int
    stock_status: StockStatus
    last_updated: Optional[datetime] = None  # Made this field optional

    class Config:
        from_attributes = True

class ItemStockResponse(BaseModel):
    item_name: str
    item_code: str
    branch_name: str
    current_stock: int
    reserved_stock: int
    available_stock: int

class ItemStockAcrossBranches(BaseModel):
    item_name: str
    item_code: str
    branch_name: str
    branch_code: str
    current_stock: int
    available_stock: int

class LowStockItem(BaseModel):
    item_name: str
    item_code: str
    available_stock: int
    minimum_stock_level: int
    shortage: int

class OutOfStockItem(BaseModel):
    item_name: str
    item_code: str
    minimum_stock_level: int

class StockAdjustment(BaseModel):
    item_id: int
    branch_id: int
    quantity: int
    adjustment_type: Literal['IN', 'ADJUSTMENT']
    reference_type: str
    reference_id: Optional[int] = None
    updated_by: int
    notes: Optional[str] = None

class StockReservation(BaseModel):
    item_id: int
    branch_id: int
    quantity: int