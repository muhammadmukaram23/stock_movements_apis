from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoleBase(BaseModel):
    role_name: str
    role_description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    role_description: Optional[str] = None

class RoleInDB(RoleBase):
    role_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # orm_mode in older Pydantic versions

class RoleResponse(RoleInDB):
    pass

class RoleSummary(BaseModel):
    role_id: int
    role_name: str