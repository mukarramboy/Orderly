from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, OrderItem, Order, ProductReview


@receiver(post_save, sender=Order)
def generate_order_numbery(sender, instance, created, **kwargs):
    if created and not instance.order_number:
        instance.order_number = f'ORD-{instance.id:06d}'
        instance.save(update_fields=['order_number'])


@receiver(post_save, sender=OrderItem)
def update_order_item_total(sender, instance, created, **kwargs):
    if created and instance.product:
        if instance.order.status in [Order.Status.CANCELED, Order.Status.REFUNDED]:
            product = Product.objects.select_for_update().get(id=instance.product.id)
            product.quantity += instance.quantity
            product.save(update_fields=['quantity', 'updated_at'])
            
        