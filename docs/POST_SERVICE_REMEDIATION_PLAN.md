# Post Service Remediation Plan

## Overview
This document maps findings from `INITIAL_FILES_AUDIT.md` directly to the current Post Service codebase (`post-service-feature-post-module`), establishing resolution statuses, technical approaches, affected files, and concrete verification criteria across all project phases.

---

## 1. Audit Findings Mapping & Status

| Audit ID | Finding Description | Severity | Current Code Status | Verification & Plan |
|---|---|---|---|---|
| **P1** | Register and login return HTTP 500 (`auth_service` queries non-DB `models/user.py`) | **Critical** | **Still Present** (`app/models/user.py` is a Pydantic model; `auth_service.py` fails when attempting DB queries on it). | Add real SQLAlchemy DB model `User` with persistent columns (`id`, `uuid`, `username`, `email`, `hashed_password`, `created_at`). Add Alembic migration `002_add_users_table.py`. |
| **P2** | JWT Token mismatch: Login puts email in `sub`, while protected routes expect canonical integer / ID. | **Critical** | **Still Present** (`app/api/auth.py` puts `sub: email`, while `app/core/security.py` requires int `sub`/`user_id`). | Update `app/core/security.py` and `app/api/auth.py` to issue and accept standard JWT with `sub: str(uuid)` and `user_id: int` claims (preserving backward compatibility for int `user_id` and supporting UUID/int conversions seamlessly). |
| **P3** | Post visibility & authorization gaps: Private / followers-only posts accessible via detail, list, search; interactions not restricted by visibility. | **High** | **Still Present** (`get_post_by_id`, `list_posts`, `comments`, `likes`, `saves`, `shares` do not consistently enforce post visibility check for private/followers). | Implement centralized authorization helper `can_access_post(post, current_user_id, is_follower=False)`. Enforce across read detail, list filtering, comments, likes, saves, shares. |
| **P4** | Media files publicly accessible via open static mount regardless of post visibility. | **Medium** | **Still Present** (`app/main.py` mounts `/static/uploads` directly to all traffic). | Protect media streaming: add route `/api/v1/media/{media_id}/file` or ensure visibility verification on private media access, preventing unauthenticated leakage. |
| **P5** | Upload file read entirely into memory (`await file.read()`) before size check. | **Medium** | **Still Present** (`app/services/media_service.py` executes `content = await file.read()` before comparing length). | Stream chunk-by-chunk with running byte count check; raise 413 immediately if limit exceeded. |
| **P6** | Following/mentions call non-existent `USER_SERVICE_URL`. | **High** | **Still Present** (`integrations/user_client.py` has stubbed httpx calls). | Maintain safe fallback / fail-soft behavior so service runs independently; support configurable user service or local mock follow table where appropriate. |
| **P7** | Missing local user model and social features. | **High** | **Still Present** (No users table; social graph externalized). | Create real `users` table with auth and password hashing. |
| **P8** | No rate limiting; password validation missing; duplicate email/username crashes. | **Medium** | **Still Present** (No duplicate checks or status 409 returned; basic password validation missing). | Enforce password complexity (min length), handle `IntegrityError` / unique checks with HTTP 409 Conflict. Add rate-limiting support. |
| **P9** | Dead legacy files in `app/api/` (`bookmarks.py`, `users.py`, `comments.py`, etc.). | **Low** | **Still Present** (`app/api/*.py` unmounted duplicates). | Safely clean up / retire unused legacy duplicate files while preserving required routes and test imports. |
| **P10** | Python 3.9 in Dockerfile vs Python 3.11/3.14 in ecosystem; `/docs` exposed in production. | **Low** | **Still Present** (`Dockerfile` uses `python:3.9-slim`). | Update Dockerfile to supported Python version (`3.11-slim`), make `/docs` conditionally disabled if `ENVIRONMENT == "production"`. |
| **X1** | Multiple identity schemes across services. | **P0** | **Pending** | Support UUID in `sub` and canonical integer `user_id` claim in JWT. |
| **X3** | Default secrets committed in config and compose. | **P0** | **Still Present** (`config.py` has fallback `super_secret_jwt_key_change_in_production`). | Enforce required `SECRET_KEY` in production; refuse startup without explicit secure configuration. Provide `.env.example`. |
| **S1 & S2** | Explore compatibility: Lowercase enum `public`, ISO timestamps, Explore API contracts. | **P0** | **Verified in Explore client** | Explore uses `GET /api/v1/posts?visibility=public` and `GET /api/v1/hashtags/{tag}/posts`. Validate response structures, media aliases (`url`, `file_url`), and datetime serialization. |

---

## 2. Implementation Phases & Tasks

### Phase 2: Critical Correctness & Authentication
1. **User Database Model & Schema:**
   - Define SQLAlchemy `User` model in `app/models/user.py` with `id` (Integer PK), `uuid` (UUID/String), `username` (unique index), `email` (unique index), `hashed_password` (String), `is_active` (Boolean), `created_at` (DateTime).
   - Create Alembic migration `002_add_users_table.py`.
2. **Auth Service & Route Remediation:**
   - Update `app/services/auth_service.py` to perform DB queries against the real `User` model.
   - Enforce password hashing with bcrypt, input validation, and password strength rules.
   - Catch unique constraint collisions and raise HTTP 409 Conflict for duplicate username or email.
   - Update `app/api/auth.py` login endpoint to emit tokens with `sub: str(user.uuid)` (or user.id) and `user_id: user.id`.
3. **JWT Identity Resolution:**
   - In `app/core/security.py`, adapt `get_current_user_id` to handle tokens where `sub` or `user_id` is present, parsing canonical integer user ID or UUID.
4. **Post Visibility & Authorization Enforcement:**
   - In `app/services/post_service.py`, `app/services/comment_service.py`, `app/services/like_service.py`, `app/services/save_service.py`, `app/services/share_service.py`:
     - Disallow reading or interacting with PRIVATE posts unless caller is the author.
     - Disallow reading or interacting with FOLLOWERS posts unless caller is author or follower.
     - Return HTTP 404 (or 403 where appropriate) to prevent information disclosure.
5. **Secrets & Production Hardening:**
   - Validate `SECRET_KEY` in `app/core/config.py`. If `ENVIRONMENT == "production"`, refuse default development secrets.

### Phase 3: Database & Migrations
1. Add `alembic/versions/002_add_users_table.py`.
2. Ensure `alembic upgrade head` and downgrade work cleanly.

### Phase 4: Dockerization & Environment
1. Update `Dockerfile` to `python:3.11-slim` (or current stable slim).
2. Ensure non-root `appuser`, healthcheck, proper volume mounts, and startup migration execution.
3. Update `docker-compose.yml` and `.env.example` with non-secret placeholders and proper port mapping (`8004` or configured `PORT`).

### Phase 5: Explore Service Compatibility
1. Write integration test exercising `/api/v1/posts?visibility=public` and `/api/v1/hashtags/{hashtag}/posts`.
2. Verify datetime ISO-8601 formatting and media URL aliases (`url` / `file_url`).

### Phase 6: Media Upload Streaming & Protection
1. Implement chunked streaming upload in `app/services/media_service.py` to enforce file size limits without buffering entire file in memory.
2. Protect media access so private post media cannot be openly scraped via URL.

### Phase 7: Dead Code Cleanup & Rate Limiting
1. Remove dead/broken unmounted legacy files in `app/api/` (`bookmarks.py`, `users.py`, `comments.py`, `likes.py`, `posts.py`, `health.py`, `dependencies.py`).
2. Add security headers and rate limiting where appropriate.

### Phase 8 & 9: Testing & Documentation
1. Run full test suite including auth, authorization, visibility, explore compatibility, and media streaming tests.
2. Provide `docs/DOCKER_SETUP.md` and updated `README.md`.
