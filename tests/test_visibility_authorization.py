import pytest
from app.models.post import PostVisibility


def test_private_post_visibility_authorization(client, user1_headers, user2_headers):
    # User 1 creates a private post
    create_res = client.post(
        "/api/v1/posts/",
        json={"caption": "My secret trading idea", "visibility": "private"},
        headers=user1_headers,
    )
    assert create_res.status_code == 201
    post_id = create_res.json()["id"]

    # 1. Author (User 1) can read private post detail
    res_author = client.get(f"/api/v1/posts/{post_id}", headers=user1_headers)
    assert res_author.status_code == 200
    assert res_author.json()["id"] == post_id

    # 2. Anonymous user cannot read private post (404)
    res_anon = client.get(f"/api/v1/posts/{post_id}")
    assert res_anon.status_code == 404

    # 3. Another user (User 2) cannot read private post (404)
    res_unauth = client.get(f"/api/v1/posts/{post_id}", headers=user2_headers)
    assert res_unauth.status_code == 404

    # 4. User 2 cannot comment on private post (403 or 404)
    res_comment = client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "Trying to spy"},
        headers=user2_headers,
    )
    assert res_comment.status_code in (403, 404)

    # 5. User 2 cannot like private post (403 or 404)
    res_like = client.post(
        f"/api/v1/posts/{post_id}/likes",
        headers=user2_headers,
    )
    assert res_like.status_code in (403, 404)

    # 6. User 2 cannot save private post (403 or 404)
    res_save = client.post(
        f"/api/v1/posts/{post_id}/save",
        headers=user2_headers,
    )
    assert res_save.status_code in (403, 404)

    # 7. User 2 cannot share private post (403 or 404)
    res_share = client.post(
        f"/api/v1/posts/{post_id}/shares",
        headers=user2_headers,
    )
    assert res_share.status_code in (403, 404)

    # 8. Private post does not appear in public listing for User 2
    res_list = client.get("/api/v1/posts/?visibility=public", headers=user2_headers)
    assert res_list.status_code == 200
    returned_ids = [p["id"] for p in res_list.json()]
    assert post_id not in returned_ids


def test_public_post_accessible_anonymously(client, user1_headers):
    create_res = client.post(
        "/api/v1/posts/",
        json={"caption": "Public analysis #BTC", "visibility": "public"},
        headers=user1_headers,
    )
    assert create_res.status_code == 201
    post_id = create_res.json()["id"]

    res_anon = client.get(f"/api/v1/posts/{post_id}")
    assert res_anon.status_code == 200
    assert res_anon.json()["id"] == post_id
