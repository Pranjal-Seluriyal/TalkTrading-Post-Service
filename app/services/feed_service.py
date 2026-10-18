from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.post import Post
from app.repositories.feed_repository import FeedRepository
from app.integrations.user_client import UserServiceClient


async def generate_feed(
    db: Session,
    current_user_id: Optional[int] = None,
    cursor_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10,
) -> Tuple[List[Post], int, Optional[int], bool]:
    feed_repo = FeedRepository(db)

    author_ids = []
    if current_user_id:
        user_client = UserServiceClient()
        author_ids = await user_client.get_following_author_ids(current_user_id)

    return feed_repo.get_feed(
        current_user_id=current_user_id,
        author_ids=author_ids,
        cursor_id=cursor_id,
        page=page,
        limit=limit,
    )
