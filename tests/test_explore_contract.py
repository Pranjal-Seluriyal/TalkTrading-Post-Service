import io
import pytest

VALID_PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"


def test_explore_candidate_posts_contract(client, user1_headers):
    # Create a public post with hashtags and caption
    create_res = client.post(
        "/api/v1/posts/",
        json={"caption": "Bitcoin breaks 70k! #crypto #bitcoin", "visibility": "public"},
        headers=user1_headers,
    )
    assert create_res.status_code == 201
    post_id = create_res.json()["id"]

    # Attach media
    dummy_file = ("chart.png", io.BytesIO(VALID_PNG_HEADER), "image/png")
    media_res = client.post(
        f"/api/v1/posts/{post_id}/media",
        files={"file": dummy_file},
        headers=user1_headers,
    )
    assert media_res.status_code == 201

    # Explore calls: GET /api/v1/posts?page=1&limit=20&visibility=public
    response = client.get("/api/v1/posts?page=1&limit=20&visibility=public")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) >= 1

    post_dto = next((p for p in posts if p["id"] == post_id), None)
    assert post_dto is not None

    # Explore contract requirements:
    assert "id" in post_dto
    assert "author_id" in post_dto
    assert post_dto["visibility"] == "public"  # Must be lowercase string
    assert "status" in post_dto
    assert "like_count" in post_dto
    assert "comment_count" in post_dto
    assert "save_count" in post_dto
    assert "share_count" in post_dto
    assert "created_at" in post_dto
    assert "updated_at" in post_dto
    assert "media_items" in post_dto

    # Media items alias contract:
    assert len(post_dto["media_items"]) >= 1
    media_item = post_dto["media_items"][0]
    assert "id" in media_item
    assert "media_type" in media_item
    assert "url" in media_item
    assert "file_url" in media_item
    assert media_item["file_url"] == media_item["url"]


def test_explore_hashtag_posts_contract(client, user1_headers):
    # Explore calls: GET /api/v1/hashtags/{hashtag}/posts?page=1&limit=20
    response = client.get("/api/v1/hashtags/crypto/posts?page=1&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert "hashtag" in data
    assert data["hashtag"] == "crypto"
    assert "posts" in data
    assert isinstance(data["posts"], list)
    assert "total" in data
