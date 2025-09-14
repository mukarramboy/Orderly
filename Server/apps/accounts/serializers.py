from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings
import random
import string

User = get_user_model()

class Stage1Serializer(serializers.Serializer):
    email_or_phone = serializers.CharField(max_length=100)

    def validate_email_or_phone(self, value):
        if '@' in value:
            if not value.endswith(('@gmail.com', '@yahoo.com', '@outlook.com')):
                raise serializers.ValidationError("Неверный email")
        else:
            if not value.isdigit() or len(value) < 10:
                raise serializers.ValidationError("Неверный телефон")
        if User.objects.filter(email=value).exists() or User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Пользователь уже существует")
        return value

    def create_otp(self, value):
        otp = ''.join(random.choices(string.digits, k=6))
        if '@' in value:
            send_mail(
                'Код верификации',
                f'Ваш код: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [value],
                fail_silently=False,
            )
            self.context['session']['temp_email'] = value
            self.context['session']['otp'] = otp
            self.context['session'].modified = True
        else:
            self.context['session']['temp_phone'] = value
            self.context['session']['otp'] = otp
            self.context['session'].modified = True
        return otp

class Stage2Serializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        session = self.context['session']
        otp = session.get('otp')
        if not otp or value != otp:
            raise serializers.ValidationError("Неверный код")
        return value

class Stage3Serializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, min_length=3)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username занят")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create_user(self):
        session = self.context['session']
        email_or_phone = session.get('temp_email') or session.get('temp_phone')
        user = User.objects.create_user(
            email=email_or_phone if '@' in email_or_phone else None,
            phone=email_or_phone if '@' not in email_or_phone else None,
            username=self.validated_data['username'],
            password=self.validated_data['password'],
        )
        if '@' in email_or_phone:
            user.is_email_verified = True
        else:
            user.is_phone_verified = True
        user.save()
        if 'otp' in session:
            del session['otp']
            session.modified = True
        return user

class Stage4Serializer(serializers.ModelSerializer):
    bio = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = User
        fields = ['avatar', 'bio']

    def update(self, instance, validated_data):
        instance.bio = validated_data.get('bio', instance.bio)
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
        instance.save()
        return instance