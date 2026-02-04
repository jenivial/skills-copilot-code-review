"""
Announcement endpoints for the High School Management System API
"""

from datetime import date, datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

ALLOWED_LEVELS = {"info", "success", "warning"}


class AnnouncementCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=280)
    start_date: Optional[str] = None
    end_date: str
    level: Optional[str] = "info"


class AnnouncementUpdate(BaseModel):
    message: Optional[str] = Field(None, min_length=1, max_length=280)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    level: Optional[str] = None


def parse_date(value: Optional[str]) -> Optional[date]:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def normalize_level(value: Optional[str]) -> str:
    if not value:
        return "info"
    normalized = value.lower()
    return normalized if normalized in ALLOWED_LEVELS else "info"


def serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": doc.get("_id"),
        "message": doc.get("message"),
        "start_date": doc.get("start_date"),
        "end_date": doc.get("end_date"),
        "level": doc.get("level", "info"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def require_teacher(teacher_username: Optional[str]) -> None:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")


def is_active_announcement(doc: Dict[str, Any], today: date) -> bool:
    start = parse_date(doc.get("start_date"))
    end = parse_date(doc.get("end_date"))
    if not end:
        return False
    if start and today < start:
        return False
    return today <= end


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get active announcements with valid date windows."""
    today = date.today()
    announcements = []

    for doc in announcements_collection.find({}):
        if is_active_announcement(doc, today):
            announcements.append(serialize_announcement(doc))

    announcements.sort(key=lambda item: item.get("end_date") or "9999-12-31")
    return announcements


@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements (requires teacher authentication)."""
    require_teacher(teacher_username)
    announcements = [serialize_announcement(doc) for doc in announcements_collection.find({})]
    announcements.sort(key=lambda item: item.get("created_at") or "")
    return announcements


@router.post("", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementCreate,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Create a new announcement (requires teacher authentication)."""
    require_teacher(teacher_username)

    start_date = parse_date(payload.start_date)
    end_date = parse_date(payload.end_date)

    if not end_date:
        raise HTTPException(status_code=400, detail="Invalid request")

    if start_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="Invalid request")

    announcement_id = uuid.uuid4().hex
    now_iso = datetime.utcnow().isoformat()
    record = {
        "_id": announcement_id,
        "message": payload.message.strip(),
        "start_date": payload.start_date or None,
        "end_date": payload.end_date,
        "level": normalize_level(payload.level),
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        announcements_collection.insert_one(record)
    except Exception:
        logger.exception("Failed to create announcement")
        raise HTTPException(status_code=500, detail="Request failed")

    return serialize_announcement(record)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdate,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an announcement (requires teacher authentication)."""
    require_teacher(teacher_username)

    update_fields: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}

    if payload.message is not None:
        update_fields["message"] = payload.message.strip()

    if payload.start_date is not None:
        start_date = parse_date(payload.start_date)
        if payload.start_date and not start_date:
            raise HTTPException(status_code=400, detail="Invalid request")
        update_fields["start_date"] = payload.start_date or None

    if payload.end_date is not None:
        end_date = parse_date(payload.end_date)
        if not end_date:
            raise HTTPException(status_code=400, detail="Invalid request")
        update_fields["end_date"] = payload.end_date

    if payload.level is not None:
        update_fields["level"] = normalize_level(payload.level)

    existing = announcements_collection.find_one({"_id": announcement_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    start = parse_date(update_fields.get("start_date", existing.get("start_date")))
    end = parse_date(update_fields.get("end_date", existing.get("end_date")))
    if not end or (start and start > end):
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        announcements_collection.update_one({"_id": announcement_id}, {"$set": update_fields})
    except Exception:
        logger.exception("Failed to update announcement")
        raise HTTPException(status_code=500, detail="Request failed")

    updated = announcements_collection.find_one({"_id": announcement_id})
    return serialize_announcement(updated)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Delete an announcement (requires teacher authentication)."""
    require_teacher(teacher_username)

    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
