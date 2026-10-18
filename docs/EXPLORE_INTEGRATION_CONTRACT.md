# Explore Integration API Contract & Compatibility Specification

## Overview
The **Explore Microservice** is a standalone Spring Boot service that generates personalized and discovery feeds by polling the **Post Service**. This document describes the exact HTTP contract implemented by Post Service to maintain complete compatibility with Explore.

---

## 1. Network Endpoint & Base URL
- **Service Name**: `post-service`
- **Default Port**: `8000` (Internal container) / `8004` (Docker Host) / `8000` (Local dev fallback)
- **Base Path**: `/api/v1`

---

## 2. Endpoints Consumed by Explore

### A. Candidate Posts for Feed Scoring
- **HTTP Method**: `GET`
- **Path**: `/api/v1/posts`
- **Query Parameters**:
  - `page` (integer, ge=1, e.g. `1`)
  - `limit` (integer, ge=1, le=100, e.g. `100` or `20`)
  - `visibility` (string, e.g. `public` — must be lowercase)
- **Response Format**: `List[ExternalPostDto]` (JSON Array of objects)
- **Status Code**: `200 OK`

#### Response Item JSON Schema:
```json
{
  "id": 101,
  "author_id": 42,
  "caption": "Bitcoin reaching new ATH! #crypto #trading",
  "visibility": "public",
  "status": "active",
  "like_count": 15,
  "comment_count": 4,
  "save_count": 8,
  "share_count": 2,
  "created_at": "2026-10-18T16:00:00Z",
  "updated_at": "2026-10-18T16:05:00Z",
  "media_items": [
    {
      "id": 1,
      "post_id": 101,
      "media_type": "image",
      "storage_key": "uuid.png",
      "url": "/static/uploads/uuid.png",
      "file_url": "/static/uploads/uuid.png",
      "thumbnail_url": null,
      "width": 1080,
      "height": 1080,
      "position": 0,
      "created_at": "2026-10-18T16:00:00Z"
    }
  ]
}
```

### B. Hashtag Posts Discovery
- **HTTP Method**: `GET`
- **Path**: `/api/v1/hashtags/{hashtag}/posts`
- **Path Parameters**:
  - `hashtag` (string without `#`, e.g. `crypto`)
- **Query Parameters**:
  - `page` (integer, ge=1)
  - `limit` (integer, ge=1, le=100)
- **Response Format**: Object
- **Status Code**: `200 OK`

#### Response JSON Schema:
```json
{
  "hashtag": "crypto",
  "posts": [ ... ],
  "total": 1
}
```

---

## 3. Critical Compatibility Guardrails

1. **Visibility Enum Format**:
   - Post Service accepts lowercase `public`, `followers`, `private`. Explore explicitly sends `visibility=public`.
2. **Media URL Aliases**:
   - Spring Boot Explore DTO expects either `file_url` or `url`. Both fields are populated identically by Post Service.
3. **Date-Time Serialization**:
   - Timestamps are returned in ISO-8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`), correctly parsed by Explore's `FlexibleInstantDeserializer`.
4. **Resilience & Fallbacks**:
   - Explore's circuit breaker triggers graceful fallback (empty list) if Post Service is temporarily offline or unreachable.
