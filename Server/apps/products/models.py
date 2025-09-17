from django.db import models


# Create your models here.
class Product(models.Model):
    seller = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)  # остаток на складе
    created_at = models.DateTimeField(auto_now_add=True)

# Заказ
class Order(models.Model):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "В обработке"),
            ("paid", "Оплачен"),
            ("shipped", "Отправлен"),
            ("delivered", "Доставлен"),
        ],
        default="pending",
    )

# Позиция в заказе
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # фиксируем цену на момент заказа