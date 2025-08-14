
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from typing import Optional
from enum import Enum
class NextTransferNumberResponse(BaseModel):
    next_transfer_number: str

class ItemAvailabilityResponse(BaseModel):
    item_name: str
    item_code: str
    available_stock: int
    availability_status: str

class SystemStatisticsResponse(BaseModel):
    total_branches: int
    total_users: int
    total_items: int
    pending_transfers: int
    total_stock_units: int