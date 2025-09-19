from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)


    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'В ожидании'
        PROCESSING = 'PROCESSING', 'В обработке'
        COMPLETED = 'COMPLETED', 'Завершен'
        CANCELED = 'CANCELED', 'Отменен'

    buyer = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, related_name="orders", null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.id} by {self.buyer.email if self.buyer else "Unknown"}'
    
    def calculate_total(self):
        total = sum(item.price * item.quantity for item in self.items.all())
        self.total_price = total
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) 

    class Meta:
        unique_together = ('order', 'product')
    
    def __str__(self):
        return f'{self.product.title if self.product else "Unknown Product"} x {self.quantity}'
    
    @property
    def cost(self):
        return self.price * self.quantity
    
    def save(self, *args, **kwargs):
        if not self.price and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)
    
    