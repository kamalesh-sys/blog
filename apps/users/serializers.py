from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers


User = get_user_model()


def validate_and_normalize_phone_no(value):
    clean_value = value.strip()
    if clean_value == "":
        return ""

    only_digits = "".join(character for character in clean_value if character.isdigit())
    if len(only_digits) != 10:
        raise serializers.ValidationError("Phone number must be exactly 10 digits.")

    return only_digits


class UserSerializer(serializers.ModelSerializer):
    def validate_phone_no(self, value):
        return validate_and_normalize_phone_no(value)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "bio",
            "phone_no",
            "profile_pic",
            "dob",
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    email = serializers.EmailField(required=True, allow_blank=False, allow_null=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "display_name",
            "bio",
            "phone_no",
            "profile_pic",
            "dob",
        ]
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
        return clean_value.lower()

    def validate_phone_no(self, value):
        return validate_and_normalize_phone_no(value)

    def validate(self, attrs):
        errors = {}
        username = attrs.get("username", "").strip()
        email = attrs.get("email", "").strip().lower()

        if username and User.objects.filter(username__iexact=username).exists():
            errors["username"] = ["A user with this username already exists."]

        if email and User.objects.filter(email__iexact=email).exists():
            errors["email"] = ["A user with this email already exists."]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        username = validated_data.get("username")
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        display_name = validated_data.get("display_name", "")
        bio = validated_data.get("bio", "")
        phone_no = validated_data.get("phone_no", "")
        profile_pic = validated_data.get("profile_pic", "")
        dob = validated_data.get("dob")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            bio=bio,
            phone_no=phone_no,
            profile_pic=profile_pic,
            dob=dob,
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
