import random
from django.core.mail import send_mail
from .models import EmailVerificationCode, User


def send_verification_code(user: User):
    code = str(random.randint(100000, 999999))  # 6-значный код
    EmailVerificationCode.objects.create(user=user, code=code)

    send_mail(
        subject="Your verification code",
        message=f"Your code is: {code}. It will expire in 5 minutes.",
        from_email=None,
        recipient_list=[user.email],
    )
