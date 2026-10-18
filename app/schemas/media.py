from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import Optional
from app.models.media import MediaType


class MediaResponse(BaseModel):
    id: int
    post_id: int
    media_type: MediaType
    storage_key: str
    url: str
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    position: int
    created_at: datetime

    @computed_field
    @property
    def file_url(self) -> str:
        return self.url

    model_config = {
        "from_attributes": True
    }
