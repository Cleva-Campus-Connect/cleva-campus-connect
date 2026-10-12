from unittest import result
from uuid import UUID
from fastapi import Depends, HTTPException, APIRouter, status, Query
from typing import Optional
from postgrest import CountMethod

from app.database import supabase
from app.dependencies import require_role
from app.schema.community import CommunityResponse, CommunityCreate, CommunityList, CommunityUpdate
from slugify import slugify

Admin_Roles = ("super_admin", "head_of_campus_leads")
All_Roles = ("super_admin", "head_of_campus_leads", "campus_lead", "ambassador" )
router = APIRouter(prefix="/admin/communities", tags=["Admin : communities"])

def make_slug(name:str)->str: # takes a text and return text tahts the function type and retturn type
    base =slugify(name)
    slug = base
    number =2 
    while True:
        found = supabase.table("communities").select("community_id").eq("slug", slug).execute()
        if not found.data:
            return slug
        slug = f"{base}-{number}"
        number +=1

@router.post("", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED )
def create_community(
        data: CommunityCreate,
        user: dict = Depends(require_role(*Admin_Roles)),
):
    row= data.model_dump()
    row["slug"] = make_slug(data.name)
    try:
        community = supabase.table("communities").insert(row).execute()
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not create community" )

    return community.data[0]

@router.get("", response_model=CommunityList, status_code=status.HTTP_200_OK)
def list_communities(
        q:Optional[str] = None,
        state: Optional[str] = None,
        community_status: Optional[str] = Query(default=None, alias="status"),
        page: int = Query(default=1 , ge=1),
        page_size: int = Query(default=20 , ge=1, le=100),
        user:dict = Depends(require_role(*All_Roles)),
):
    query= supabase.table("communities").select("*", count=CountMethod.exact)
    if user["role"] not in Admin_Roles:
        query = query.eq("community_id", user["community_id"])
    if q:
        clean = q.replace(",", "").replace("(", "").replace(")", "").replace("%", "").strip()
        if clean:
            query =query.or_(
                f"name.ilike.%{clean}%,school.ilike.%{clean}%,state.ilike.%{clean}%"
            )
    if state:
        query = query.eq("state", state)
    if community_status:
        query = query.eq("status", community_status)

    start =(page - 1) * page_size
    end = start + page_size - 1
    results =  query.order("created_at", desc=True).range(start, end).execute()


    return {
        "items" :  results.data,
        "total" :  results.count,
        "page" : page,
        "page_size" : page_size,


    }

@router.get("/{community_id}", response_model=CommunityResponse, status_code=status.HTTP_200_OK)
def get_one_community(
        community_id: UUID,
        user: dict = Depends(require_role(*All_Roles)),
):
    if user["role"] not in Admin_Roles and str(community_id) != user["community_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not Allowed")

    results = (
        supabase.table("communities").select("*").eq("community_id", community_id).limit(1).execute()
    )
    if not results.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")

    return results.data[0]


# @router.put("/{community_id}", status_code=status.HTTP_202_ACCEPTED, response_model=CommunityResponse)
# def update_one_community(
#         community_id: UUID,
#         data: CommunityUpdate,
#         user: dict = Depends(require_role(*All_Roles)),
# ):
    # is_admin = user["role"] in Admin_Roles

    # if not is_admin and str(community_id) != user["community_id"]:
    #     raise HTTPException(status.HTTP_403_FORBIDDEN, "Not Allowed")

    # change = data.model_dump(exclude_unset=True)
    # if not change:
    #     raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing  to update")
    # if not is_admin and "status" in change:
    #     raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can change status")

    # try:
    #     results = (
    #         supabase.table("communities").update(change).eq("community_id", str(community_id)).execute()
    #     )
    # except Exception:
    #     raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not update community")
    # if not results.data:
    #     raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")

    # return results.data[0]

@router.patch("/{community_id}", status_code=status.HTTP_202_ACCEPTED, response_model=CommunityResponse)
def update_community(
        community_id: UUID,
        data: CommunityUpdate,
        user: dict = Depends(require_role(*All_Roles))
):
    is_admin = user["role"] in Admin_Roles
    if not is_admin and str(community_id) != user["community_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not Allowed")

    change= data.model_dump(exclude_unset=True)
    if not change:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing  to update")

    if not is_admin and "status" in change:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can change status")

    try:
        results = (
            supabase.table("communities").update(change).eq("community_id", community_id).execute()
        )
    except Exception as e:
        print( "Update error:",e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not update community")

    if not results.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")

    return results.data[0]

@router.patch("/{community_id}/archive", response_model=CommunityResponse, status_code = status.HTTP_202_ACCEPTED)
def archive_community(
        community_id: UUID,
        user:dict = Depends(require_role(*Admin_Roles)),
):
    results= (
        supabase.table("communities").update({"status" : "archived"}).eq("community_id", str(community_id)).execute()
    )
    if not results.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")
    return results.data[0]
