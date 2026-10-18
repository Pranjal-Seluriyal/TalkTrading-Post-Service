from typing import Optional, List
from app.models.post import Post, PostVisibility, PostStatus


def can_user_view_post(
    post: Optional[Post],
    current_user_id: Optional[int] = None,
    following_author_ids: Optional[List[int]] = None,
) -> bool:
    """
    Centralized visibility authorization check.
    - If post is None or DELETED, return False.
    - If post is PUBLIC, any user (including anonymous) can view.
    - If post is PRIVATE, only the author can view.
    - If post is FOLLOWERS:
        * Author can always view.
        * If following_author_ids is provided and author_id in following_author_ids, allow.
        * Otherwise disallow.
    """
    if post is None:
        return False

    if post.status == PostStatus.DELETED:
        return False

    if post.visibility == PostVisibility.PUBLIC:
        return True

    # For non-public posts, anonymous users have no access
    if current_user_id is None:
        return False

    # Author always has access to their own posts
    if post.author_id == current_user_id:
        return True

    # Followers visibility
    if post.visibility == PostVisibility.FOLLOWERS:
        if following_author_ids and post.author_id in following_author_ids:
            return True
        return False

    # Private posts only accessible to author
    if post.visibility == PostVisibility.PRIVATE:
        return False

    return False


def can_user_interact_with_post(
    post: Optional[Post],
    current_user_id: int,
    following_author_ids: Optional[List[int]] = None,
) -> bool:
    """
    Check if an authenticated user can interact (comment, like, save, share) with a post.
    Must be active and visible to the user.
    """
    if post is None or post.status != PostStatus.ACTIVE:
        return False

    return can_user_view_post(
        post=post,
        current_user_id=current_user_id,
        following_author_ids=following_author_ids,
    )
