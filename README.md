## Run

```bash
python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000/
API base: http://127.0.0.1:8000/api/

## Swagger / OpenAPI Docs

Interactive API documentation is exposed via `drf-spectacular`:

- Schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/swagger/`
- ReDoc: `GET /api/docs/redoc/`

Generate or refresh the schema artifact:

```bash
python manage.py spectacular --file schema.yml --validate
```

For authenticated endpoints in Swagger UI, use:
`Token <your_auth_token>`

## Email Notifications

Email notifications are sent instantly for:
- follow
- like
- comment.
- profile picture update
- login.

```bash
DEFAULT_FROM_EMAIL=no-reply@yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
```

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
