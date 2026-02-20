from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    phone_no = models.CharField(max_length=20, blank=True)
    profile_pic = models.URLField(blank=True)
    dob = models.DateField(blank=True, null=True)

    def __str__(self):
        if self.display_name:
            return self.display_name
        return self.username
