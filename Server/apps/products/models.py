from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError("Категория не может быть родителем самой себя")
        
        # Проверка на циклические зависимости
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("Обнаружена циклическая зависимость в категориях")
                current = current.parent


class Product(models.Model):
    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)   

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['seller', 'is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def clean(self):
        if self.price <= 0:
            raise ValidationError("Цена должна быть больше нуля")
        if self.quantity < 0:
            raise ValidationError("Количество не может быть отрицательным")
        if self.old_price and self.old_price <= self.price:
            raise ValidationError("Старая цена должна быть больше текущей цены")



class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'В ожидании'
        PROCESSING = 'PROCESSING', 'В обработке'
        COMPLETED = 'COMPLETED', 'Завершен'
        CANCELED = 'CANCELED', 'Отменен'
        REFUNDED = 'REFUNDED', 'Возвращен'

    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, related_name="orders", null=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    # Связаные с ценой
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Доставка")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    shipping_address = models.CharField(max_length=255)

    shipping_phone = models.CharField(max_length=20, verbose_name="Телефон получателя")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="Отправлен")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Доставлен")


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Order {self.id} by {self.buyer.email if self.buyer else "Unknown"}'
    
    
    def calculate_totals(self):
        """Расчет всех сумм заказа"""
        # Подитог
        subtotal = self.items.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')
        
        self.subtotal = subtotal
        
        # Итоговая сумма
        self.total_price = self.subtotal + self.shipping_cost
        
        # Сохраняем только измененные поля
        self.save(update_fields=['subtotal', 'total_price', 'updated_at'])

    def can_be_canceled(self):
        """Проверка, можно ли отменить заказ"""
        return self.status in [self.Status.PENDING, self.Status.PROCESSING]
    
    def can_be_refunded(self):
        """Проверка, можно ли вернуть заказ"""
        return self.status in [self.Status.DELIVERED, self.Status.COMPLETED]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('order', 'product')
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
    
    def __str__(self):
        return f'{self.product.title if self.product else "Unknown Product"} x {self.quantity}'
    
    @property
    def total_cost(self):
        return self.price * self.quantity
    
    def save(self, *args, **kwargs):
        if not self.price and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Количество должно быть больше нуля")
        if self.price < 0:
            raise ValidationError("Цена не может быть отрицательной")
        

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", db_index=True)
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_main = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'sort_order']),
        ]

    def __str__(self):
        return f'Image for {self.product.title if self.product else "Unknown Product"}'
    

    def save(self, *args, **kwargs):
        if self.is_main or not self.product.images.exists():
            self.product.images.update(is_main=False)
            self.is_main = True
        super().save(*args, **kwargs)

    
class ProductReview(models.Model):

    class Rating(models.IntegerChoices):
        ONE = 1, '1 звезда'
        TWO = 2, '2 звезды'
        THREE = 3, '3 звезды'
        FOUR = 4, '4 звезды'
        FIVE = 5, '5 звезд'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='reviews',
    )

    rating = models.IntegerField(
        choices=Rating.choices,
        verbose_name="Рейтинг"
    )
    title = models.CharField(max_length=255)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"Отзыв на {self.product.title} от {self.user.email}"
    