from os.path import exists
from typing import Optional
from postgrest import CountMethod
from unittest import result
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from slugify import slugify

from app.database import supabase
from app.dependencies import require_role
from app.routers import community
from app.routers.community import Admin_Roles
from app.schema.ambassador import AmbassadorAdmin, AmbassadorCreate, AmbassadorUpdate, AmbassadorAdminList, AmbassadorRoles, AmbassadorStatus

router = APIRouter(prefix="/admin/ambassador", tags=["Admin: Ambassadors"])

Admin_Roles = ("super_admin", "head_of_campus_leads")
Add_Roles = ("super_admin", "head_of_campus_leads", "campus_lead", "co_lead")

def make_unique_slugify(name:str)->str:
    base  = slugify(name) or "ambassador"
    slug = base
    number =2
    while True:
        found = (
            supabase.table("ambassadors").select("ambassador_id").eq("slug", slug)
            .execute()
        )
        if not found.data:
            return slug
        slug = f"{base}-{number}"
        number += 1
@router.post("", response_model=AmbassadorAdmin, status_code=status.HTTP_201_CREATED)
def create_ambassador(data: AmbassadorCreate, user : dict = Depends(require_role(*Add_Roles))
                      ):
    if user["role"] not in Admin_Roles and str(data.community_id) != user["community_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only add to your campus leads")

    community = (
        supabase.table("communities").select(
            "community_id" ).eq("community_id", str(data.community_id)).neq("status","archived").limit(1).execute()
    )
    if not community.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Community not found")

    row = data.model_dump(mode="json")
    row["slug"] = make_unique_slugify(data.full_name)

    try:
        results = supabase.table("ambassadors").insert(row).execute()
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not create Ambassador")

    return  results.data[0]

@router.patch("/{ambassador_id}", status_code=status.HTTP_200_OK, response_model=AmbassadorAdmin)
def update_ambassador(ambassador_id: UUID, data:AmbassadorUpdate, user : dict = Depends(require_role(*Admin_Roles))):
    existing = (supabase.table("ambassadors").select("ambassador_id, community_id" ).
                eq("ambassador_id", str(ambassador_id))
                .limit(1).execute())
    if not existing.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ambassador not found")

    is_admin = user["role"] in Admin_Roles
    if not is_admin and existing.data[0]["community_id"] != user["community_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="You can only update your campus Ambassador")

    change = data.model_dump(exclude_unset = True, mode="json")
    if not change:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    if not is_admin and "status" in change:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admin can change status")

    try:
        results = (
            supabase.table("ambassadors").update(change).eq("ambassador_id", str(ambassador_id)).execute()
        )
    except Exception:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Could not update Ambassador")

    return results.data[0]

@router.get("", response_model=AmbassadorAdminList)
def list_ambassadors(
    q: Optional[str] = None,
    community_id: Optional[UUID] = None,
    role: Optional[AmbassadorRoles] = None,
    ambassador_status: Optional[AmbassadorStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(require_role(*Add_Roles)),
):
    query = supabase.table("ambassadors").select("*", count=CountMethod.exact)

    if user["role"] in Admin_Roles:
        if community_id:
            query = query.eq("community_id", str(community_id))
    else:
        query = query.eq("community_id", user["community_id"])

    if q:
        clean = q.replace(",", "").replace("(", "").replace(")", "").replace("%", "").strip()
        if clean:
            query = query.ilike("full_name", f"%{clean}%")
    if role:
        query = query.eq("role", role)
    if ambassador_status:
        query = query.eq("status", ambassador_status)

    start = (page - 1) * page_size
    end = start + page_size - 1
    results = query.order("full_name").range(start, end).execute()

    return {
        "items": results.data,
        "total": results.count,
        "page": page,
        "page_size": page_size,
    }

@router.patch("/{ambassador_id}/archive", status_code=status.HTTP_200_OK, response_model=AmbassadorAdmin)
def archive_ambassador(
        ambassador_id: UUID,
        user: dict = Depends(require_role(*Add_Roles)),
):
    try:
        results = (
            supabase.table("ambassadors").update({"status": "archived"}).eq("ambassador_id", str(ambassador_id)).execute()
        )
    except Exception:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Could not archive Ambassador")

    if not results.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ambassador not found")

    return results.data[0]