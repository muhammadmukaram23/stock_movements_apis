from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    category_name: str
    category_code: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    description: Optional[str] = None

class CategoryInDB(CategoryBase):
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # or orm_mode=True in older Pydantic versions

class CategoryResponse(CategoryInDB):
    pass

class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    category_code: str