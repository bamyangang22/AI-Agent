from pydantic import BaseModel
from typing import Optional


class RestaurantContext(BaseModel):
    customer_name: str
    table_number: Optional[int] = None
    party_size: Optional[int] = None


class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    has_inappropriate_language: bool
    reason: Optional[str] = None


class OutputGuardrailOutput(BaseModel):
    is_inappropriate: bool
    reason: Optional[str] = None
    safe_response: Optional[str] = None


class HandoffData(BaseModel):
    to_agent_name: str
    reason: str
    issue_type: str
    issue_description: str