from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Register, Transaction, Profile

# Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=Register.objects.all(), message="An account with this email already exists.")]
    )

    class Meta:
        model = Register
        fields = ['username', 'email', 'password', 'dob', 'security_question', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        return Register.objects.create(**validated_data)


# Login Serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = Register.objects.get(email=email, password=password)
        except Register.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        data['user'] = user
        return data


# Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo_url:
            return request.build_absolute_uri(obj.photo_url.url)
        return None

    class Meta:
        model = Profile
        fields = '__all__'


# Transaction Serializer
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
