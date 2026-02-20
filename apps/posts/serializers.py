from rest_framework import serializers

from .models import Comment, Post, Tag


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "name",
            "content",
            "image",
            "category",
            "author",
            "author_username",
            "likes_count",
            "comments_count",
            "tags",
            "tag_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]

    def validate_name(self, value):
        clean_value = value.strip()
        if clean_value == "":
            raise serializers.ValidationError("Post name cannot be empty.")
        return clean_value

    def validate_content(self, value):
        clean_value = value.strip()
        if clean_value == "":
            raise serializers.ValidationError("Post content cannot be empty.")
        return clean_value

    def validate_image(self, value):
        return value.strip()

    def validate_category(self, value):
        return value.strip()

    def validate_tag_names(self, value):
        cleaned_names = []
        seen = set()

        for item in value:
            clean_item = item.strip()
            if clean_item == "":
                raise serializers.ValidationError("Tag names cannot be empty.")

            normalized = clean_item.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned_names.append(clean_item)

        return cleaned_names

    def _save_tags(self, post, tag_names):
        if tag_names is None:
            return

        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        post.tags.set(tags)

    def create(self, validated_data):
        tag_names = validated_data.pop("tag_names", [])
        post = super().create(validated_data)
        self._save_tags(post, tag_names)
        return post

    def update(self, instance, validated_data):
        tag_names = validated_data.pop("tag_names", None)
        post = super().update(instance, validated_data)
        self._save_tags(post, tag_names)
        return post


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author",
            "author_username",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["post", "author", "created_at", "updated_at"]

    def validate_content(self, value):
        clean_value = value.strip()
        if clean_value == "":
            raise serializers.ValidationError("Comment content cannot be empty.")
        return clean_value
