from unittest import result

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify

from app.database import supabase
from app.dependencies import require_role
from app.routers import community
from app.routers.community import Admin_Roles
from app.schema.ambassador import AmbassadorAdmin, AmbassadorCreate

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