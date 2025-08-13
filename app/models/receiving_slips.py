from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ConditionOnArrival(str, Enum):
    GOOD = "GOOD"
    DAMAGED = "DAMAGED"
    PARTIAL = "PARTIAL"

class ReceivingSlipBase(BaseModel):
    transfer_id: int
    dispatch_id: int
    received_by: int
    condition_on_arrival: ConditionOnArrival = ConditionOnArrival.GOOD
    notes: Optional[str] = None
    photo_path: Optional[str] = None

class ReceivingSlipCreate(ReceivingSlipBase):
    pass

class ReceivingSlipItem(BaseModel):
    item_id: int
    dispatched_quantity: int
    received_quantity: int
    damaged_quantity: int = 0
    condition_notes: Optional[str] = None

class ReceivingSlipResponse(ReceivingSlipBase):
    receiving_id: int
    receiving_number: str
    receiving_date: datetime
    transfer_number: Optional[str] = None
    dispatch_number: Optional[str] = None
    from_branch: Optional[str] = None
    to_branch: Optional[str] = None
    received_by_name: Optional[str] = None

class ReceivedItemResponse(BaseModel):
    receiving_item_id: int
    item_id: int
    item_name: str
    item_code: str
    unit_of_measure: str
    dispatched_quantity: int
    received_quantity: int
    damaged_quantity: int
    condition_notes: Optional[str] = None