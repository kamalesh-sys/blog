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

### Uploads
- `POST /api/uploads/image/` (auth required, multipart form-data)
  - field: `file`
  - allowed types: image/*
  - max size: 5MB
  - response: `{ "url": "<absolute_media_url>" }`

### Posts
- `GET /api/posts/`
- `POST /api/posts/`
- `GET /api/posts/<pk>/`
- `PUT /api/posts/<pk>/`
- `PATCH /api/posts/<pk>/`
- `DELETE /api/posts/<pk>/`
- `GET /api/users/<user_id>/posts/`
- `GET /api/users/<user_id>/liked-posts/`
- `GET /api/posts/<post_id>/comments/`
- `POST /api/posts/<post_id>/comments/`
- `POST /api/posts/<post_id>/like/`

### Query Params
- `GET /api/posts/?search=<text>` (search in post content and tags)
- `GET /api/posts/?category=<category_name>` (filter by category)
