from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

Status = Literal["active", "coming_soon", "temporarily_inactive", "archived"]

class CommunityCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=4, max_length=250, description="Community name")
    school: str = Field(min_length=1, max_length=250, description="School/Instituition name")
    description: Optional[str] = None
    state: str = Field(min_length=1, max_length=250, description="State of community")
    status: Status = "coming_soon"
    join_link: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-90, le=180)

    @model_validator(mode="after")
    def coordinates_together(self):
        if(self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude are required")
        return self

class CommunityUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field (default=None, min_length=4, max_length=250, description="Community name")
    school: Optional[str] = Field(default=None, min_length=1, max_length=250, description="School/Institution name")
    state: Optional[str] = Field(default=None, min_length=1, max_length=250, description="State of community")
    description: Optional[str] = None
    status : Optional[Status] = None
    join_link: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

class CommunityResponse(BaseModel):
    community_id: UUID
    name:str
    slug:str
    school:str
    state:str
    description:Optional[str]
    status:str
    join_link:Optional[str]
    latitude:Optional[float]
    longitude:Optional[float]
    created_at: datetime
    updated_at: datetime

class CommunityList(BaseModel):
    items: List[CommunityResponse]
    total: int
    page: int
    page_size: int

class CommunityPublic(BaseModel):
    community_id: UUID
    name: str
    slug: str
    school: str
    state: str
    description: Optional[str]
    status: str
    join_link: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

class CommunityPublicList(BaseModel):
    items: List[CommunityPublic]
    total: int
    page: int
    page_size: int