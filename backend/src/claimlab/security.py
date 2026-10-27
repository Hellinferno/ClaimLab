"""Authentication, CSRF verification, and guest session management."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from claimlab.config import settings
from claimlab.database import get_db
from claimlab.models import GuestOwner

GUEST_COOKIE_NAME = "claimlab_guest"
GUEST_DURATION_HOURS = 24


def hash_token(token: str) -> str:
    """Generate SHA-256 HMAC of token using SESSION_SECRET."""
    return hmac.new(settings.SESSION_SECRET.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_guest_credential() -> Tuple[str, str, str, str]:
    """Generates (raw_cookie_token, cookie_hash, raw_csrf_token, csrf_hash)."""
    raw_cookie = secrets.token_urlsafe(32)
    cookie_hash = hash_token(raw_cookie)
    raw_csrf = secrets.token_urlsafe(32)
    csrf_hash = hash_token(raw_csrf)
    return raw_cookie, cookie_hash, raw_csrf, csrf_hash


def create_guest(db: Session) -> Tuple[GuestOwner, str, str]:
    """Creates a new guest owner in database and returns (owner, raw_cookie, raw_csrf)."""
    raw_cookie, cookie_hash, raw_csrf, csrf_hash = generate_guest_credential()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=GUEST_DURATION_HOURS)

    owner = GuestOwner(
        credential_hash=cookie_hash,
        csrf_secret_hash=csrf_hash,
        created_at=now,
        expires_at=expires,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner, raw_cookie, raw_csrf


def get_current_guest(
    request: Request,
    claimlab_guest: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> GuestOwner:
    """FastAPI dependency to authenticate guest owner from cookie."""
    if not claimlab_guest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "GUEST_REQUIRED", "message": "Guest cookie is missing"},
        )

    token_hash = hash_token(claimlab_guest)
    now = datetime.now(timezone.utc)

    owner = (
        db.query(GuestOwner)
        .filter(
            GuestOwner.credential_hash == token_hash,
            GuestOwner.deleted_at.is_(None),
            GuestOwner.expires_at > now,
        )
        .first()
    )

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "GUEST_EXPIRED", "message": "Guest session invalid or expired"},
        )

    return owner


def verify_csrf(
    request: Request,
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
    guest: GuestOwner = None,
) -> None:
    """Verifies CSRF token on mutating requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Check origin
    origin = request.headers.get("origin")
    if origin and origin != settings.PUBLIC_ORIGIN and settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ORIGIN_REJECTED", "message": f"Invalid request origin: {origin}"},
        )

    if not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CSRF", "message": "X-CSRF-Token header is required"},
        )

    expected_hash = hash_token(x_csrf_token)
    if not guest or not hmac.compare_digest(guest.csrf_secret_hash, expected_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CSRF", "message": "Invalid CSRF token"},
        )
