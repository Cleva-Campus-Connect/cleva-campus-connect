from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

AmbassadorRoles = Literal[
    "campus_lead", "co_lead",  "ambassador"
]
AmbassadorStatus = Literal["pending_review", "published", "paused", "archived"]

class Ambassador(BaseModel):
    ambassador_id: UUID
    full_name: str
    role: AmbassadorRoles
    slug: str
    bio: Optional[str] = None
    photo: Optional[str] = None
    links: list[dict[str,str]] = []

class AmbassadorList(BaseModel):
        items: list[Ambassador]

class AmbassadorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    community_id: UUID
    full_name: str = Field(max_length=200, min_length=2)
    role: AmbassadorRoles
    bio: Optional[str] = Field(default=None, max_length=2000)
    photo: Optional[str] = None
    links: list[dict[str,str]] = []

class AmbassadorAdmin(BaseModel):
    ambassador_id: UUID
    community_id: UUID
    full_name: str
    bio: Optional[str] = None
    photo: Optional[str] = None
    links: list[dict[str,str]] = []
    status: AmbassadorStatus

class AmbassadorUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Optional[str] = Field(default=None, max_length=200, min_length=2)
    role: Optional[AmbassadorRoles] = None
    bio: Optional[str] = Field(default=None, max_length=2000)
    photo: Optional[str] = None
    links: Optional[list[dict[str,str]]] = None
    status: Optional[AmbassadorStatus] = None

class AmbassadorAdminList(BaseModel):
    items: list[AmbassadorAdmin]
    total: int
    page: int
    page_size: int