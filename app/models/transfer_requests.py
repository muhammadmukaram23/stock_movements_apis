from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TransferStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class TransferPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class TransferRequestBase(BaseModel):
    from_branch_id: int
    to_branch_id: int
    priority: TransferPriority = TransferPriority.MEDIUM
    notes: Optional[str] = None

class TransferRequestCreate(TransferRequestBase):
    requested_by: int

class TransferRequestItem(BaseModel):
    item_id: int
    requested_quantity: int
    notes: Optional[str] = None

class TransferRequestUpdate(BaseModel):
    status: Optional[TransferStatus] = None
    rejection_reason: Optional[str] = None
    approved_by: Optional[int] = None

class TransferRequestResponse(TransferRequestBase):
    transfer_id: int
    transfer_number: str
    status: TransferStatus
    requested_by: int
    requested_by_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    from_branch_name: Optional[str] = None
    to_branch_name: Optional[str] = None
    request_date: datetime
    approval_date: Optional[datetime] = None
    dispatch_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TransferRequestItemResponse(BaseModel):
    request_item_id: int
    item_id: int
    item_name: str
    item_code: str
    unit_of_measure: str
    requested_quantity: int
    approved_quantity: Optional[int] = None
    available_stock: int
    notes: Optional[str] = None

class TransferRequestSummary(BaseModel):
    transfer_id: int
    transfer_number: str
    from_branch: str  # Added back
    to_branch: str
    requested_by: str
    status: TransferStatus  # Added back
    priority: TransferPriority
    request_date: datetime
    notes: Optional[str] = None
    total_items: int
