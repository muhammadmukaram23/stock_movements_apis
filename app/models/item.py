from pydantic import BaseModel, condecimal
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    item_name: str
    item_code: str
    category_id: int
    description: Optional[str] = None
    unit_of_measure: Optional[str] = 'PCS'
    minimum_stock_level: Optional[int] = 0
    maximum_stock_level: Optional[int] = 1000
    unit_price: Optional[condecimal(max_digits=10, decimal_places=2)] = 0.00
    is_active: Optional[bool] = True

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    unit_of_measure: Optional[str] = None
    minimum_stock_level: Optional[int] = None
    maximum_stock_level: Optional[int] = None
    unit_price: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    is_active: Optional[bool] = None

# Response models
class ItemResponse(BaseModel):
    item_id: int
    item_name: str
    item_code: str
    category_id: int  # This is required in the base model
    category_name: str  # This comes from the JOIN
    description: Optional[str] = None
    unit_of_measure: Optional[str] = 'PCS'
    minimum_stock_level: Optional[int] = 0
    maximum_stock_level: Optional[int] = 1000
    unit_price: Optional[condecimal(max_digits=10, decimal_places=2)] = 0.00
    is_active: Optional[bool] = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ItemSummary(BaseModel):
    item_id: int
    item_name: str
    item_code: str
    category_name: str

class ItemDetailResponse(ItemBase):
    item_id: int
    category_name: str
    created_at: datetime
    updated_at: datetime

class ItemCategoryResponse(BaseModel):
    item_id: int
    item_name: str
    item_code: str
    unit_of_measure: str