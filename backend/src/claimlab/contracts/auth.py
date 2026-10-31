"""Contracts for guest identity, CSRF tokens, and account info."""
from typing import Any, Dict
from pydantic import ConfigDict
from claimlab.contracts.common import StrictModel


class GuestSessionResponse(StrictModel):
    expires_at: str
    csrf_token: str


class MeResponse(StrictModel):
    model_config = ConfigDict(protected_namespaces=())

    guest_id: str
    expires_at: str
    model_mode: str
    limits: Dict[str, Any]
    web_research: bool = False


class DeleteDataResponse(StrictModel):
    deletion_id: str
    status: str = "deleted"
