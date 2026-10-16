from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from slugify import slugify

from app.database import supabase
from app.dependencies import require_role
from app.schema.event import (
    EventAdmin,
    EventAdminList,
    EventCreate,
    EventStatus,
    EventUpdate,
)

router = APIRouter(prefix="/admin/events", tags=["Admin: Events"])

ADMIN_ROLES = ("super_admin", "head_of_campus_leads")
ADD_ROLES = ADMIN_ROLES + ("campus_lead", "co_lead")


def make_unique_slug(title: str) -> str:
    base = slugify(title) or "event"
    slug = base
    number = 2
    while True:
        found = (
            supabase.table("events")
            .select("event_id")
            .eq("slug", slug)
            .execute()
        )
        if not found.data:
            return slug
        slug = f"{base}-{number}"
        number += 1


@router.get("", response_model=EventAdminList)
def list_events(
    status_filter: Optional[EventStatus] = Query(default=None, alias="status"),
    community_id: Optional[UUID] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(require_role(*ADMIN_ROLES)),
):
    query = supabase.table("events").select("*", count="exact")

    if status_filter:
        query = query.eq("status", status_filter)
    if community_id:
        query = query.eq("community_id", str(community_id))

    start = (page - 1) * page_size
    end = start + page_size - 1

    result = (
        query.order("start_time", desc=True)
        .range(start, end)
        .execute()
    )

    return {
        "items": result.data,
        "total": result.count or 0,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=EventAdmin, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate,
    user: dict = Depends(require_role(*ADD_ROLES)),
):
    if user["role"] not in ADMIN_ROLES and str(data.community_id) != user["community_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only add to your own campus")

    community = (
        supabase.table("communities")
        .select("community_id")
        .eq("community_id", str(data.community_id))
        .neq("status", "archived")
        .limit(1)
        .execute()
    )
    if not community.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")

    row = data.model_dump(mode="json")
    row["slug"] = make_unique_slug(data.title)

    try:
        result = supabase.table("events").insert(row).execute()
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not create event")

    return result.data[0]


@router.patch("/{event_id}", response_model=EventAdmin)
def update_event(
    event_id: UUID,
    data: EventUpdate,
    user: dict = Depends(require_role(*ADD_ROLES)),
):
    existing = (
        supabase.table("events")
        .select("event_id, community_id")
        .eq("event_id", str(event_id))
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")

    is_admin = user["role"] in ADMIN_ROLES
    if not is_admin and existing.data[0]["community_id"] != user["community_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your campus")

    change = data.model_dump(exclude_unset=True, mode="json")
    if not change:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    if not is_admin and "status" in change:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can change status")

    try:
        result = (
            supabase.table("events")
            .update(change)
            .eq("event_id", str(event_id))
            .execute()
        )
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not update event")

    return result.data[0]
