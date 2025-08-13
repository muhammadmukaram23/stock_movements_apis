from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from enum import Enum

class DispatchBase(BaseModel):
    transfer_id: int
    dispatched_by: int
    loader_name: Optional[str] = None
    vehicle_info: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None



class DispatchCreate(BaseModel):
    transfer_id: int
    dispatched_by: int
    loader_name: Optional[str] = None
    vehicle_info: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None

class DispatchResponse(BaseModel):
    dispatch_id: int
    dispatch_number: str
    transfer_id: int
    transfer_number: Optional[str] = None
    from_branch: Optional[str] = None
    to_branch: Optional[str] = None
    dispatched_by: int
    dispatched_by_name: Optional[str] = None
    loader_name: Optional[str] = None
    vehicle_info: Optional[str] = None
    dispatch_date: datetime
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None

class DispatchItemResponse(BaseModel):
    item_id: int
    item_name: str
    item_code: str
    dispatched_quantity: int
    unit_of_measure: str