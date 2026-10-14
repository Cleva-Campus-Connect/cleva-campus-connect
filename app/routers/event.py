from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify

from app.database import supabase
from app.dependencies import require_role
from app.schema.event import EventAdmin, EventCreate

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