from rest_framework import serializers
from .models import Category, Product, Order, OrderItem, ProductImage, ProductReview
from django.db import transaction


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'is_active', 'sort_order', 
                  'created_at', 'updated_at', 'children']
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_main', 'sort_order', 'created_at']
        read_only_fields = ['created_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_email', 'rating', 'title', 
                  'comment', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_approved']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'price', 'old_price', 'quantity', 
                  'category_name', 'main_image', 'is_active']
    
    def get_main_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.user.email', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'seller', 'seller_name', 'category', 'category_name', 
                  'title', 'slug', 'description', 'price', 'old_price', 'quantity',
                  'is_active', 'created_at', 'updated_at', 'images', 'reviews', 
                  'average_rating']
        read_only_fields = ['seller', 'slug', 'created_at', 'updated_at']
    
    def get_reviews(self, obj):
        approved_reviews = obj.reviews.filter(is_approved=True)
        return ProductReviewSerializer(approved_reviews, many=True).data
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['category', 'title', 'description', 'price', 'old_price', 
                  'quantity', 'is_active']
    
    def validate(self, data):
        if data.get('price', 0) <= 0:
            raise serializers.ValidationError({"price": "Цена должна быть больше нуля"})
        if data.get('old_price') and data.get('old_price') <= data.get('price', 0):
            raise serializers.ValidationError(
                {"old_price": "Старая цена должна быть больше текущей цены"}
            )
        return data


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_title', 'quantity', 'price', 'total_cost']
        read_only_fields = ['price', 'total_cost']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'buyer', 'buyer_email', 'order_number', 'status', 
                  'status_display', 'subtotal', 'shipping_cost', 'total_price',
                  'shipping_address', 'shipping_phone', 'created_at', 'updated_at',
                  'shipped_at', 'delivered_at', 'items']
        read_only_fields = ['buyer', 'order_number', 'subtotal', 'total_price', 
                            'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'shipping_phone', 'shipping_cost', 'items']
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Заказ должен содержать хотя бы один товар")
        
        for item in value:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Каждый товар должен содержать product_id и quantity"
                )
            if item['quantity'] <= 0:
                raise serializers.ValidationError("Количество должно быть больше нуля")
        
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Генерация номера заказа
        import uuid
        order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        
        # Создание заказа
        order = Order.objects.create(
            buyer=user,
            order_number=order_number,
            **validated_data
        )
        
        # Создание элементов заказа
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            
            # Проверка наличия товара
            if product.quantity < item_data['quantity']:
                raise serializers.ValidationError(
                    f"Недостаточно товара {product.title} на складе"
                )
            
            # Создание элемента заказа
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price
            )
            
            # Уменьшение количества товара
            product.quantity -= item_data['quantity']
            product.save(update_fields=['quantity'])
        
        # Расчет итоговых сумм
        order.calculate_totals()
        
        return order