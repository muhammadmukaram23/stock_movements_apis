from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from typing import Optional
class DashboardSummaryResponse(BaseModel):
    items_in_stock: int
    low_stock_items: int
    pending_requests: int
    pending_dispatches: int
    incoming_shipments: int

class RecentActivityResponse(BaseModel):
    activity_type: str
    reference: str
    description: str
    activity_date: datetime
