from django.contrib import admin

from .models import Comment, Post, PostLike, Tag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "author", "created_at")
	search_fields = ("name", "author__username")
	list_filter = ("created_at",)
	filter_horizontal = ("tags",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ("id", "post", "author", "created_at")
	search_fields = ("post__name", "author__username")
	list_filter = ("created_at",)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
	list_display = ("id", "post", "user", "created_at")
	search_fields = ("post__name", "user__username")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "created_at")
	search_fields = ("name",)
