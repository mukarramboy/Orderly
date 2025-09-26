from rest_framework import serializers
from .models import Category, Product, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'children']

    def get_children(self, obj):
        return CategorySerializer(obj.children.all(), many=True).data


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField() 
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'category', 'title',
            'description', 'price', 'quantity',
            'created_at', 'updated_at'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price', 'cost']


class OrderSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField()
    items = OrderItemSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'status', 'shipping_address',
            'total_price', 'created_at', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        order.update_total()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Обновляем данные заказа
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем товары заказа
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        instance.update_total()
        return instance
