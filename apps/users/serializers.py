from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "display_name", "bio"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "display_name", "bio"]
        read_only_fields = ["id"]

    def validate_username(self, value):
        clean_value = value.strip()
        if clean_value == "":
            raise serializers.ValidationError("Username is required.")
        return clean_value

    def validate_email(self, value):
        clean_value = value.strip()
        if clean_value == "":
            raise serializers.ValidationError("Email is required.")
        return clean_value

    def create(self, validated_data):
        username = validated_data.get("username")
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        display_name = validated_data.get("display_name", "")
        bio = validated_data.get("bio", "")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            bio=bio,
        )

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = ""
        password = ""

        if "username" in attrs and attrs["username"] is not None:
            username = attrs["username"].strip()

        if "password" in attrs and attrs["password"] is not None:
            password = attrs["password"]

        if username == "":
            raise serializers.ValidationError("Username and password are required.")

        if password == "":
            raise serializers.ValidationError("Username and password are required.")

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid credentials.")

        attrs["user"] = user
        return attrs
