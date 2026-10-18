from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user_id
from app.schemas.media import MediaResponse
from app.services.media_service import add_media_to_post, delete_media

router = APIRouter(
    tags=["Media"],
)


@router.post("/posts/{post_id}/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_post_media(
    post_id: int,
    file: UploadFile = File(...),
    position: int = Form(0),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Upload and attach image/video media item to a post. Restricted to post author."""
    result = await add_media_to_post(
        db=db,
        post_id=post_id,
        file=file,
        current_user_id=current_user_id,
        position=position,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found",
        )

    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to attach media to this post",
        )

    return result


@router.delete("/media/{media_id}")
async def remove_post_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Delete a media item from storage and database. Restricted to post author."""
    result = await delete_media(db=db, media_id=media_id, current_user_id=current_user_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media item with ID {media_id} not found",
        )

    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this media item",
        )

    return {"message": "Media item deleted successfully"}


import os
from fastapi.responses import FileResponse
from app.core.security import get_optional_user_id
from app.core.authorization import can_user_view_post
from app.integrations.user_client import UserServiceClient
from app.repositories.media_repository import MediaRepository
from app.repositories.post_repository import PostRepository
from app.core.config import settings


@router.get("/media/{media_id}/file")
async def get_media_file(
    media_id: int,
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id),
):
    """Serve media file while strictly enforcing the parent post's visibility permissions."""
    media = MediaRepository(db).get_by_id(media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media item with ID {media_id} not found",
        )

    post = PostRepository(db).get_by_id(media.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent post not found or inactive",
        )

    following_ids = []
    if current_user_id:
        user_client = UserServiceClient()
        following_ids = await user_client.get_following_author_ids(current_user_id)

    if not can_user_view_post(post, current_user_id=current_user_id, following_author_ids=following_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media item with ID {media_id} not found",
        )

    safe_key = os.path.basename(media.storage_key)
    file_path = os.path.realpath(os.path.join(settings.LOCAL_STORAGE_DIR, safe_key))
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found on disk",
        )

    return FileResponse(file_path)
