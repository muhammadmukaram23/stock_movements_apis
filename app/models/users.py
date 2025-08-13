from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Base models
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    branch_id: int
    role_id: int
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password_hash: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    new_password_hash: str

# Response models
class UserLoginResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str]
    branch_id: int
    branch_name: str
    branch_code: str
    role_id: int
    role_name: str
    is_active: bool
    last_login: Optional[datetime]

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str]
    branch_name: str
    role_name: str
    is_active: bool
    created_at: datetime

class UserDetailResponse(UserBase):
    user_id: int
    branch_name: str
    role_name: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

class UserSummary(BaseModel):
    user_id: int
    username: str
    full_name: str
    role_name: str
    is_active: bool

class UserPermissions(BaseModel):
    role_name: str
    role_description: Optional[str]