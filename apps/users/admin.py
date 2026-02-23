from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("id", "username", "email", "display_name", "is_staff", "is_active")
    search_fields = ("username", "email", "display_name")

    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("display_name", "bio")}),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following", "created_at")
    search_fields = ()
    list_filter = ("created_at",)
