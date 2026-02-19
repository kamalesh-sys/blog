# Blog API (Django + DRF)

This project is a simple Blog API with:
- User registration and login (token-based auth)
- Post CRUD
- Tags on posts
- Comments on posts
- Like/unlike toggle for posts

All endpoints are under:
- `http://127.0.0.1:8000/api/`

## 1) Quick Start

Run these commands in project root (`d:\DjangoProjects\blog`):

```bash
python manage.py migrate
python manage.py runserver
```

Server will run at:
- `http://127.0.0.1:8000/`

## 2) Postman Setup (Beginner Friendly)

In Postman:
1. Create an environment variable `base_url`
2. Set `base_url = http://127.0.0.1:8000/api`
3. For JSON requests, add header:
   - `Content-Type: application/json`
4. For protected endpoints, add header:
   - `Authorization: Token <your_token_here>`

Important:
- Token format must be exactly: `Token abc123...`
- Do not use `Bearer` for this project.

## 3) Standard Error Response Format

All errors now return a consistent JSON structure.

Validation errors (`400 Bad Request`):

```json
{
  "success": false,
  "status_code": 400,
  "message": "Validation error.",
  "errors": {
    "field_name": ["error message"]
  }
}
```

Auth/permission/not-found errors (`401`, `403`, `404`):

```json
{
  "success": false,
  "status_code": 401,
  "message": "Authentication credentials were not provided."
}
```

## 4) Authentication Endpoints

### Register User

- Method: `POST`
- URL: `{{base_url}}/auth/register/`
- Auth: Not required

Body (raw JSON):

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "strong-pass-123",
  "first_name": "Alice",
  "last_name": "Johnson",
  "display_name": "Alice J",
  "bio": "I write about Django."
}
```

Success response (`201 Created`) includes user data + token:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Johnson",
  "display_name": "Alice J",
  "bio": "I write about Django.",
  "token": "your_generated_token"
}
```

Possible errors:
- `400 Bad Request` for missing/invalid fields
- Password must be at least 8 characters

### Login User

- Method: `POST`
- URL: `{{base_url}}/auth/login/`
- Auth: Not required

Body (raw JSON):

```json
{
  "username": "alice",
  "password": "strong-pass-123"
}
```

Success response (`200 OK`):

```json
{
  "token": "your_generated_token"
}
```

Possible errors:
- `400 Bad Request` with `"Invalid credentials."`
- `400 Bad Request` with `"Username and password are required."`

### Get Current Logged-In User

- Method: `GET`
- URL: `{{base_url}}/auth/me/`
- Auth: Required (`Authorization: Token <token>`)
- Body: None

Success response (`200 OK`):

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Johnson",
  "display_name": "Alice J",
  "bio": "I write about Django."
}
```

Possible errors:
- `401 Unauthorized` if token is missing/invalid

## 5) Post Endpoints

Post object in responses:

```json
{
  "id": 1,
  "name": "My first post",
  "content": "Hello world",
  "author": 1,
  "author_username": "alice",
  "likes_count": 0,
  "comments_count": 0,
  "tags": ["django", "api"],
  "created_at": "2026-02-19T12:34:56.000000Z",
  "updated_at": "2026-02-19T12:34:56.000000Z"
}
```

`tag_names` is write-only:
- Send it in request body for create/update.
- It will not appear in response.
- Response uses `tags`.

### List All Posts

- Method: `GET`
- URL: `{{base_url}}/posts/`
- Auth: Not required
- Body: None

Success response (`200 OK`): array of post objects.

### Create Post

- Method: `POST`
- URL: `{{base_url}}/posts/`
- Auth: Required

Body (raw JSON):

```json
{
  "name": "Django tips",
  "content": "Always validate data.",
  "tag_names": ["django", "backend", "api"]
}
```

Notes:
- `name` and `content` cannot be empty.
- `tag_names` is optional.
- If tag does not exist, it is created automatically.
- Duplicate tag names are ignored (case-insensitive check in serializer).

Success response (`201 Created`): post object with `tags`.

Possible errors:
- `401 Unauthorized` if not logged in
- `400 Bad Request` for invalid fields

### Get One Post

- Method: `GET`
- URL: `{{base_url}}/posts/<post_id>/`
- Auth: Not required
- Body: None

Success response (`200 OK`): single post object.

Possible errors:
- `404 Not Found` if post does not exist

### Update Full Post

- Method: `PUT`
- URL: `{{base_url}}/posts/<post_id>/`
- Auth: Required (owner only)

Body (raw JSON):

```json
{
  "name": "Updated title",
  "content": "Updated content",
  "tag_names": ["python", "rest"]
}
```

Notes:
- With `PUT`, send full required post fields.

Possible errors:
- `401 Unauthorized` if not logged in
- `403 Forbidden` if logged in user is not the post owner
- `404 Not Found` if post does not exist

### Update Partial Post

- Method: `PATCH`
- URL: `{{base_url}}/posts/<post_id>/`
- Auth: Required (owner only)

Body example (raw JSON):

```json
{
  "tag_names": ["tutorial", "django"]
}
```

Notes:
- You can update only one field.
- If `tag_names` is included, tags are replaced with the provided list.
- If `tag_names` is not included, existing tags remain unchanged.
- Send `"tag_names": []` to clear all tags.

### Delete Post

- Method: `DELETE`
- URL: `{{base_url}}/posts/<post_id>/`
- Auth: Required (owner only)
- Body: None

Success response (`200 OK`):

```json
{
  "detail": "Post deleted."
}
```

Possible errors:
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

### List Posts By User

- Method: `GET`
- URL: `{{base_url}}/users/<user_id>/posts/`
- Auth: Not required
- Body: None

Success response (`200 OK`): array of posts for that user.

Possible errors:
- `404 Not Found` if user does not exist

## 6) Comment Endpoints

Comment object in responses:

```json
{
  "id": 1,
  "post": 1,
  "author": 1,
  "author_username": "alice",
  "content": "Nice post!",
  "created_at": "2026-02-19T12:35:00.000000Z",
  "updated_at": "2026-02-19T12:35:00.000000Z"
}
```

### List Comments for a Post

- Method: `GET`
- URL: `{{base_url}}/posts/<post_id>/comments/`
- Auth: Not required
- Body: None

Success response (`200 OK`): array of comments.

Possible errors:
- `404 Not Found` if post does not exist

### Add Comment to a Post

- Method: `POST`
- URL: `{{base_url}}/posts/<post_id>/comments/`
- Auth: Required

Body (raw JSON):

```json
{
  "content": "Very useful, thanks!"
}
```

Notes:
- Do not send `post` in body; post is taken from URL.
- Do not send `author`; it is set from logged-in user.

Possible errors:
- `401 Unauthorized`
- `400 Bad Request` if content is empty
- `404 Not Found` if post does not exist

## 7) Like/Unlike Endpoint

### Toggle Like

- Method: `POST`
- URL: `{{base_url}}/posts/<post_id>/like/`
- Auth: Required
- Body: None

Behavior:
- First call likes the post.
- Second call unlikes the same post.

Like response (`201 Created`):

```json
{
  "detail": "Post liked.",
  "liked": true
}
```

Unlike response (`200 OK`):

```json
{
  "detail": "Post unliked.",
  "liked": false
}
```

Possible errors:
- `401 Unauthorized`
- `404 Not Found` if post does not exist

## 8) Suggested Postman Testing Order

1. `POST /auth/register/`
2. Copy token from response
3. Set `Authorization` header to `Token <token>`
4. `POST /posts/` with `tag_names`
5. `PATCH /posts/<id>/` to update tags
6. `POST /posts/<id>/comments/`
7. `POST /posts/<id>/like/` twice to test toggle
8. `GET /auth/me/` to verify login token

## 9) Common Beginner Mistakes

- Missing `/api/` in URL
- Using `Bearer` instead of `Token`
- Forgetting `Content-Type: application/json`
- Sending empty strings for required fields
- Sending `post` or `author` in comment create body (not needed)
