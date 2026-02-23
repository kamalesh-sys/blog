import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from rest_framework import serializers


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def upload_image_file(request, image_file):
    if image_file is None:
        raise serializers.ValidationError({"file": ["No file provided."]})

    content_type = (image_file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise serializers.ValidationError({"file": ["Only image files allowed."]})

    if image_file.size > MAX_IMAGE_SIZE_BYTES:
        raise serializers.ValidationError({"file": ["Image must be under 5MB."]})

    _, extension = os.path.splitext(image_file.name or "")
    extension = extension.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = ".jpg"

    file_name = f"{get_random_string(18)}{extension}"
    storage_path = f"uploads/{file_name}"
    saved_path = default_storage.save(storage_path, image_file)
    saved_path = str(saved_path).replace("\\", "/")

    host = request.get_host()
    return f"{request.scheme}://{host}{settings.MEDIA_URL}{saved_path}"
