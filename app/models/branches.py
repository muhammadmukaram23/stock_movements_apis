from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BranchBase(BaseModel):
    branch_name: str
    branch_code: str
    city: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    branch_manager_name: Optional[str] = None
    is_active: Optional[bool] = True

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    branch_name: Optional[str] = None
    branch_code: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    branch_manager_name: Optional[str] = None
    is_active: Optional[bool] = None

class BranchInDB(BranchBase):
    branch_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # or orm_mode=True in older Pydantic versions

class BranchResponse(BranchInDB):
    pass

class BranchSummary(BaseModel):
    branch_id: int
    branch_name: str
    branch_code: str
    # Remove city and is_active since they're not in the SELECT statement