from pydantic import BaseModel
from typing import Optional


class RestaurantContext(BaseModel):
    customer_name: str
    table_number: Optional[int] = None
    party_size: Optional[int] = None


class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: Optional[str] = None


class HandoffData(BaseModel):
    to_agent_name: str
    reason: str
    issue_type: str
    issue_description: str