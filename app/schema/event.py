from typing import List, Literal, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

EventStatus = Literal["draft", "published", "cancelled", "completed", "archived"]


class EventCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    community_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    start_time: AwareDatetime
    end_time: Optional[AwareDatetime] = None
    venue: Optional[str] = Field(default=None, max_length=300)
    signup_link: Optional[str] = None

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
        return self


class EventUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    start_time: Optional[AwareDatetime] = None
    end_time: Optional[AwareDatetime] = None
    venue: Optional[str] = Field(default=None, max_length=300)
    signup_link: Optional[str] = None
    status: Optional[EventStatus] = None

    @model_validator(mode="after")
    def end_after_start(self):
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time < self.start_time
        ):
            raise ValueError("end_time cannot be before start_time")
        return self


class EventAdmin(BaseModel):
    event_id: UUID
    community_id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    start_time: AwareDatetime
    end_time: Optional[AwareDatetime] = None
    venue: Optional[str] = None
    signup_link: Optional[str] = None
    status: EventStatus
    created_at: AwareDatetime
    updated_at: AwareDatetime


class EventAdminList(BaseModel):
    items: List[EventAdmin]
    total: int
    page: int
    page_size: int