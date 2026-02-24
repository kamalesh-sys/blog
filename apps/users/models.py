from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    phone_no = models.CharField(max_length=20, blank=True)
    profile_pic = models.URLField(blank=True)
    dob = models.DateField(blank=True, null=True)
    following = models.ManyToManyField(
        "self",
        through="Follow",
        through_fields=("follower", "following"),
        symmetrical=False,
        related_name="followers",
        blank=True,
    )

    def __str__(self):
        if self.display_name:
            return self.display_name
        return self.username


class Follow(models.Model):
    follower = models.ForeignKey("User", on_delete=models.CASCADE, related_name="following_relationships")
    following = models.ForeignKey("User", on_delete=models.CASCADE, related_name="follower_relationships")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_follow_relationship",
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("following")),
                name="prevent_self_follow",
            ),
        ]
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["following"]),
        ]

    def clean(self):
        if self.follower_id == self.following_id:
            raise ValidationError("You cannot follow yourself.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.follower_id} follows {self.following_id}"
