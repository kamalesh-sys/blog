# Simple Blog API

A very simple Django REST API for users and posts.

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

### Posts
- `GET /api/posts/`
- `POST /api/posts/`
- `GET /api/posts/<pk>/`
- `PUT /api/posts/<pk>/`
- `PATCH /api/posts/<pk>/`
- `DELETE /api/posts/<pk>/`
- `GET /api/users/<user_id>/posts/`
- `GET /api/posts/<post_id>/comments/`
- `POST /api/posts/<post_id>/comments/`
- `POST /api/posts/<post_id>/like/`
