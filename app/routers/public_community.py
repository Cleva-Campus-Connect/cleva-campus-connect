from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from postgrest import CountMethod

from app.database import supabase
from app.schema.community import CommunityPublic, CommunityPublicList
from app.schema.ambassador import Ambassador, AmbassadorList

router = APIRouter(prefix="/communities", tags=["Public : communities"])

PUBLIC_COLUMNS = (
    "community_id,name,slug,school,state,description,"
    "status,join_link,latitude,longitude"
)


@router.get("", response_model=CommunityPublicList, status_code=status.HTTP_200_OK)
def list_public_communities(
        q: Optional[str] = None,
        state: Optional[str] = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
):
    query = (
        supabase.table("communities")
        .select(PUBLIC_COLUMNS, count=CountMethod.exact)
        .neq("status", "archived")
    )
    if q:
        clean = q.replace(",", "").replace("(", "").replace(")", "").replace("%", "").strip()
        if clean:
            query = query.or_(
                f"name.ilike.%{clean}%,school.ilike.%{clean}%,state.ilike.%{clean}%"
            )
    if state:
        query = query.eq("state", state)

    start = (page - 1) * page_size
    end = start + page_size - 1
    results = query.order("name").range(start, end).execute()

    return {
        "items": results.data,
        "total": results.count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{slug}", response_model=CommunityPublic, status_code=status.HTTP_200_OK)
def get_public_community(slug: str):
    results = (
        supabase.table("communities")
        .select(PUBLIC_COLUMNS)
        .eq("slug", slug)
        .neq("status", "archived")
        .limit(1)
        .execute()
    )
    if not results.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")
    return results.data[0]

Ambassador_Columns = "ambassador_id, full_name, role, slug, bio, photo, links"

@router.get("/{slug}/ambassadors", response_model=AmbassadorList, status_code=status.HTTP_200_OK)
def list_community_ambassadors(slug: str):
    community =( supabase.table ("communities").select("community_id").eq("slug", slug).neq("status", "archived").limit(1).execute() )
    if not community.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Community not found")

    results = (supabase.table("ambassadors").select(Ambassador_Columns).
               eq("community_id", community.data[0]["community_id"]).
               eq("status", "published").order("full_name").execute()
               )
    return {
        "items": results.data
    }
