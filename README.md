## Run

```bash
python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000/
API base: http://127.0.0.1:8000/api/

## Endpoints

### Auth
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET /api/auth/me/`
- `PUT /api/auth/me/`
- `PATCH /api/auth/me/`
  - supports optional multipart `file` to auto-upload and set `profile_pic`
- `POST /api/users/<user_id>/follow/` (auth required, toggle follow/unfollow)
- `GET /api/users/<user_id>/followers/` (auth required)
- `GET /api/users/<user_id>/following/` (auth required)

### Uploads
- `POST /api/uploads/image/` (auth required, multipart form-data)
  - field: `file`
  - allowed types: image/*
  - max size: 5MB
  - response: `{ "url": "<absolute_media_url>" }`
  - note: this endpoint only uploads and returns URL; it does not update `User` or `Post`

### Posts
- `GET /api/posts/`
- `POST /api/posts/`
  - supports optional multipart `file` to auto-upload and set `image`
- `GET /api/posts/following/` (auth required, posts from users you follow)
- `GET /api/posts/<pk>/`
- `PUT /api/posts/<pk>/`
- `PATCH /api/posts/<pk>/`
  - `PUT`/`PATCH` support optional multipart `file` to auto-upload and update `image`
- `DELETE /api/posts/<pk>/`
- `GET /api/users/<user_id>/posts/`
- `GET /api/users/<user_id>/liked-posts/`
- `GET /api/posts/<post_id>/comments/`
- `POST /api/posts/<post_id>/comments/`
- `POST /api/posts/<post_id>/like/`

### Query Params
- `GET /api/posts/?search=<text>` (search in post content and tags)
- `GET /api/posts/?category=<category_name>` (filter by category)
