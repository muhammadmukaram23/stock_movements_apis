
from pydantic import BaseModel,Field,field_validator

from typing import Optional, List
from datetime import date, datetime
from typing import Optional
from enum import Enum


class DiscrepancyStatus(str, Enum):
    REPORTED = "REPORTED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"

class DiscrepancyType(str, Enum):
    OVERAGE = "OVERAGE"
    SHORTAGE = "SHORTAGE"
    DAMAGED = "DAMAGED"
    LOST = "LOST"
    OTHER = "OTHER"
    EXCESS = "EXCESS"

    @classmethod
    def get_default(cls):
        return cls.OTHER

class StockDiscrepancyBase(BaseModel):
    branch_id: int = Field(..., gt=0)
    item_id: int = Field(..., gt=0)
    expected_stock: int = Field(..., ge=0)
    actual_stock: int = Field(..., ge=0)
    discrepancy_type: DiscrepancyType = Field(default=DiscrepancyType.get_default())
    investigation_notes: Optional[str] = Field(None, max_length=500)

    @field_validator('discrepancy_type', mode='before')
    def validate_discrepancy_type(cls, v):
        if v == '' or v is None:
            return DiscrepancyType.get_default()
        try:
            return DiscrepancyType(v.upper())
        except ValueError:
            return DiscrepancyType.get_default()

class StockDiscrepancyCreate(StockDiscrepancyBase):
    reported_by: int = Field(..., gt=0)

class StockDiscrepancyUpdate(BaseModel):
    investigation_notes: Optional[str] = Field(None, max_length=500)
    status: Optional[DiscrepancyStatus] = None

class StockDiscrepancyResolution(BaseModel):
    resolution_notes: str = Field(..., max_length=500)

class StockDiscrepancyResponse(BaseModel):
    discrepancy_id: int
    branch_id: int
    item_id: int
    expected_stock: int
    actual_stock: int
    difference: int
    discrepancy_type: str
    status: DiscrepancyStatus
    investigation_notes: Optional[str]
    resolution_notes: Optional[str]
    reported_by: int
    reported_by_name: str
    reported_date: datetime
    resolved_date: Optional[datetime]
    branch_name: str
    item_name: str
    item_code: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
