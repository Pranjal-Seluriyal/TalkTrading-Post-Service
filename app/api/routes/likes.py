from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user_id
from app.services.like_service import (
    like_post,
    unlike_post,
    get_like_count,
)

router = APIRouter(
    prefix="/posts",
    tags=["Likes"],
)


from app.core.authorization import can_user_interact_with_post
from app.integrations.user_client import UserServiceClient
from app.repositories.post_repository import PostRepository


@router.post("/{post_id}/likes")
async def add_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Like a post. Database enforces UNIQUE(user_id, post_id)."""
    post = PostRepository(db).get_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found or inactive",
        )

    user_client = UserServiceClient()
    following_ids = await user_client.get_following_author_ids(current_user_id)
    if not can_user_interact_with_post(post, current_user_id=current_user_id, following_author_ids=following_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to interact with this post",
        )

    result = like_post(db=db, post_id=post_id, user_id=current_user_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found or inactive",
        )

    if result == "already_liked":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Post already liked by this user",
        )

    return {"message": "Post liked successfully"}


@router.delete("/{post_id}/likes")
def remove_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Unlike a post. Idempotent operation."""
    result = unlike_post(db=db, post_id=post_id, user_id=current_user_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like relationship not found for this post",
        )

    return {"message": "Like removed successfully"}


@router.get("/{post_id}/likes/count")
def read_like_count(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get total like count for a post."""
    return {"post_id": post_id, "like_count": get_like_count(db=db, post_id=post_id)}
