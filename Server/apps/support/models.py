from django.db import models

# Create your models here.
class Chat(models.Model):
    """Чат (диалог) между двумя пользователями"""
    user1 = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="chats_as_user1"
    )
    user2 = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="chats_as_user2"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user1', 'user2'],
                name='unique_chat_between_users'
            ),
            models.CheckConstraint(
                check=~models.Q(user1=models.F("user2")),
                name="prevent_self_chat"
            ),
            models.CheckConstraint(
                check=models.Q(user1__lt=models.F("user2")),
                name="user1_lt_user2"  # гарантирует порядок user1 < user2
            ),
        ]

    def __str__(self):
        return f"Чат между {self.user1} и {self.user2}"


class Message(models.Model):
    """Сообщения внутри чата"""
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Сообщение от {self.sender} в чате {self.chat.id}"