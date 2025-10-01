from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.paginator import Paginator
from .models import Category, Product, Order, OrderItem, ProductImage, ProductReview
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, OrderSerializer, OrderCreateSerializer,
    ProductImageSerializer, ProductReviewSerializer
)
from .permissions import IsSellerOrReadOnly, IsOrderOwner


# ==================== КАТЕГОРИИ ====================

class CategoryListView(APIView):
    """
    Получить список всех активных категорий или создать новую
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить список всех активных категорий",
        responses={200: CategorySerializer(many=True)}
    )
    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Создать новую категорию",
        request_body=CategorySerializer,
        responses={201: CategorySerializer()}
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    """
    Получить, обновить или удалить конкретную категорию
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить детали категории",
        responses={200: CategorySerializer()}
    )
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug, is_active=True)
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Обновить категорию",
        request_body=CategorySerializer,
        responses={200: CategorySerializer()}
    )
    def put(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Частично обновить категорию",
        request_body=CategorySerializer,
        responses={200: CategorySerializer()}
    )
    def patch(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Удалить категорию",
        responses={204: 'Категория удалена'}
    )
    def delete(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RootCategoriesView(APIView):
    """
    Получить корневые категории (без родителей)
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Получить все корневые категории",
        responses={200: CategorySerializer(many=True)}
    )
    def get(self, request):
        categories = Category.objects.filter(is_active=True, parent=None)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CategorySubcategoriesView(APIView):
    """
    Получить подкатегории конкретной категории
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Получить подкатегории категории",
        responses={200: CategorySerializer(many=True)}
    )
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug, is_active=True)
        subcategories = category.children.filter(is_active=True)
        serializer = CategorySerializer(subcategories, many=True)
        return Response(serializer.data)


# ==================== ТОВАРЫ ====================

class ProductListView(APIView):
    """
    Получить список товаров или создать новый товар
    """
    permission_classes = [IsSellerOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить список товаров с фильтрацией и поиском",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="ID категории", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию", type=openapi.TYPE_STRING),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Максимальная цена", type=openapi.TYPE_NUMBER),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Сортировка (price, -price, created_at)", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Номер страницы", type=openapi.TYPE_INTEGER),
        ],
        responses={200: ProductListSerializer(many=True)}
    )
    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related('category', 'seller')
        
        # Фильтрация по категории
        category_id = request.query_params.get('category')
        if category_id:
            products = products.filter(category_id=category_id)
        
        # Поиск
        search = request.query_params.get('search')
        if search:
            products = products.filter(title__icontains=search)
        
        # Фильтрация по цене
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Сортировка
        ordering = request.query_params.get('ordering', '-created_at')
        products = products.order_by(ordering)
        
        # Пагинация
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(products, 20)
        page_obj = paginator.get_page(page_number)
        
        serializer = ProductListSerializer(page_obj, many=True, context={'request': request})
        
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next() and page_obj.next_page_number() or None,
            'previous': page_obj.has_previous() and page_obj.previous_page_number() or None,
            'results': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Создать новый товар (только для продавцов)",
        request_body=ProductCreateUpdateSerializer,
        responses={201: ProductDetailSerializer()}
    )
    def post(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'error': 'Только продавцы могут создавать товары'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(seller=request.user.seller_profile)
            detail_serializer = ProductDetailSerializer(product, context={'request': request})
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    """
    Получить, обновить или удалить конкретный товар
    """
    permission_classes = [IsSellerOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить детали товара",
        responses={200: ProductDetailSerializer()}
    )
    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects.select_related('category', 'seller'),
            slug=slug,
            is_active=True
        )
        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Обновить товар",
        request_body=ProductCreateUpdateSerializer,
        responses={200: ProductDetailSerializer()}
    )
    def put(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        
        # Проверка прав доступа
        if not hasattr(request.user, 'seller_profile') or product.seller != request.user.seller_profile:
            return Response(
                {'error': 'У вас нет прав на редактирование этого товара'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductCreateUpdateSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            detail_serializer = ProductDetailSerializer(product, context={'request': request})
            return Response(detail_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Частично обновить товар",
        request_body=ProductCreateUpdateSerializer,
        responses={200: ProductDetailSerializer()}
    )
    def patch(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        
        # Проверка прав доступа
        if not hasattr(request.user, 'seller_profile') or product.seller != request.user.seller_profile:
            return Response(
                {'error': 'У вас нет прав на редактирование этого товара'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductCreateUpdateSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            detail_serializer = ProductDetailSerializer(product, context={'request': request})
            return Response(detail_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Удалить товар",
        responses={204: 'Товар удален'}
    )
    def delete(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        
        # Проверка прав доступа
        if not hasattr(request.user, 'seller_profile') or product.seller != request.user.seller_profile:
            return Response(
                {'error': 'У вас нет прав на удаление этого товара'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductByCategoryView(APIView):
    """
    Получить товары по категории
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Получить товары конкретной категории",
        responses={200: ProductListSerializer(many=True)}
    )
    def get(self, request, category_slug):
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category', 'seller')
        
        # Пагинация
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(products, 20)
        page_obj = paginator.get_page(page_number)
        
        serializer = ProductListSerializer(page_obj, many=True, context={'request': request})
        
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next() and page_obj.next_page_number() or None,
            'previous': page_obj.has_previous() and page_obj.previous_page_number() or None,
            'results': serializer.data
        })


class MyProductsView(APIView):
    """
    Получить товары текущего продавца
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Получить товары текущего продавца",
        responses={200: ProductListSerializer(many=True)}
    )
    def get(self, request):
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'error': 'У вас нет профиля продавца'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        products = Product.objects.filter(
            seller=request.user.seller_profile
        ).select_related('category')
        
        # Пагинация
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(products, 20)
        page_obj = paginator.get_page(page_number)
        
        serializer = ProductListSerializer(page_obj, many=True, context={'request': request})
        
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next() and page_obj.next_page_number() or None,
            'previous': page_obj.has_previous() and page_obj.previous_page_number() or None,
            'results': serializer.data
        })


class ProductAddImageView(APIView):
    """
    Добавить изображение к товару
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Добавить изображение к товару",
        request_body=ProductImageSerializer,
        responses={201: ProductImageSerializer()}
    )
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        
        # Проверка прав доступа
        if not hasattr(request.user, 'seller_profile') or product.seller != request.user.seller_profile:
            return Response(
                {'error': 'У вас нет прав на добавление изображений к этому товару'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductAddReviewView(APIView):
    """
    Добавить отзыв к товару
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Добавить отзыв к товару",
        request_body=ProductReviewSerializer,
        responses={201: ProductReviewSerializer()}
    )
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== ЗАКАЗЫ ====================

class OrderListView(APIView):
    """
    Получить список заказов или создать новый заказ
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Получить список заказов пользователя",
        responses={200: OrderSerializer(many=True)}
    )
    def get(self, request):
        if hasattr(request.user, 'seller_profile'):
            # Продавец видит заказы со своими товарами
            orders = Order.objects.filter(
                items__product__seller=request.user.seller_profile
            ).distinct().prefetch_related('items', 'items__product')
        else:
            # Покупатель видит только свои заказы
            orders = Order.objects.filter(
                buyer=request.user
            ).prefetch_related('items', 'items__product')
        
        # Пагинация
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(orders, 20)
        page_obj = paginator.get_page(page_number)
        
        serializer = OrderSerializer(page_obj, many=True)
        
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next() and page_obj.next_page_number() or None,
            'previous': page_obj.has_previous() and page_obj.previous_page_number() or None,
            'results': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Создать новый заказ",
        request_body=OrderCreateSerializer,
        responses={201: OrderSerializer()}
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """
    Получить детали конкретного заказа
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Получить детали заказа",
        responses={200: OrderSerializer()}
    )
    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.prefetch_related('items', 'items__product'),
            pk=pk
        )
        
        # Проверка прав доступа
        if order.buyer != request.user:
            if not (hasattr(request.user, 'seller_profile') and 
                    order.items.filter(product__seller=request.user.seller_profile).exists()):
                return Response(
                    {'error': 'У вас нет доступа к этому заказу'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderCancelView(APIView):
    """
    Отменить заказ
    """
    permission_classes = [IsAuthenticated, IsOrderOwner]
    
    @swagger_auto_schema(
        operation_description="Отменить заказ",
        responses={200: OrderSerializer()}
    )
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        # Проверка прав доступа
        if order.buyer != request.user:
            return Response(
                {'error': 'Только покупатель может отменить заказ'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not order.can_be_canceled():
            return Response(
                {'error': 'Этот заказ не может быть отменен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Возвращаем товары на склад
        for item in order.items.all():
            if item.product:
                item.product.quantity += item.quantity
                item.product.save(update_fields=['quantity'])
        
        order.status = Order.Status.CANCELED
        order.save(update_fields=['status', 'updated_at'])
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderRefundView(APIView):
    """
    Запросить возврат заказа
    """
    permission_classes = [IsAuthenticated, IsOrderOwner]
    
    @swagger_auto_schema(
        operation_description="Запросить возврат заказа",
        responses={200: OrderSerializer()}
    )
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        # Проверка прав доступа
        if order.buyer != request.user:
            return Response(
                {'error': 'Только покупатель может запросить возврат'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not order.can_be_refunded():
            return Response(
                {'error': 'Этот заказ не может быть возвращен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = Order.Status.REFUNDED
        order.save(update_fields=['status', 'updated_at'])
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderUpdateStatusView(APIView):
    """
    Обновить статус заказа (только для продавца)
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Обновить статус заказа",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['PENDING', 'PROCESSING', 'COMPLETED', 'CANCELED', 'REFUNDED']
                )
            }
        ),
        responses={200: OrderSerializer()}
    )
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        # Проверка, что пользователь - продавец товаров в заказе
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {'error': 'Только продавец может обновлять статус'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not order.items.filter(product__seller=request.user.seller_profile).exists():
            return Response(
                {'error': 'У вас нет прав на обновление этого заказа'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status not in dict(Order.Status.choices):
            return Response(
                {'error': 'Недопустимый статус'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


# ==================== ОТЗЫВЫ ====================

class ReviewListView(APIView):
    """
    Получить список одобренных отзывов
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Получить список одобренных отзывов",
        manual_parameters=[
            openapi.Parameter('product', openapi.IN_QUERY, description="ID товара", type=openapi.TYPE_INTEGER),
            openapi.Parameter('rating', openapi.IN_QUERY, description="Фильтр по рейтингу", type=openapi.TYPE_INTEGER),
        ],
        responses={200: ProductReviewSerializer(many=True)}
    )
    def get(self, request):
        reviews = ProductReview.objects.filter(is_approved=True)
        
        # Фильтрация по товару
        product_id = request.query_params.get('product')
        if product_id:
            reviews = reviews.filter(product_id=product_id)
        
        # Фильтрация по рейтингу
        rating = request.query_params.get('rating')
        if rating:
            reviews = reviews.filter(rating=rating)
        
        reviews = reviews.order_by('-created_at')
        
        # Пагинация
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(reviews, 20)
        page_obj = paginator.get_page(page_number)
        
        serializer = ProductReviewSerializer(page_obj, many=True)
        
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next() and page_obj.next_page_number() or None,
            'previous': page_obj.has_previous() and page_obj.previous_page_number() or None,
            'results': serializer.data
        })


class MyReviewsView(APIView):
    """
    Получить отзывы текущего пользователя
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Получить мои отзывы",
        responses={200: ProductReviewSerializer(many=True)}
    )
    def get(self, request):
        reviews = ProductReview.objects.filter(user=request.user).order_by('-created_at')
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewDetailView(APIView):
    """
    Получить, обновить или удалить конкретный отзыв
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить детали отзыва",
        responses={200: ProductReviewSerializer()}
    )
    def get(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        serializer = ProductReviewSerializer(review)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Обновить отзыв",
        request_body=ProductReviewSerializer,
        responses={200: ProductReviewSerializer()}
    )
    def put(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        
        # Проверка прав доступа
        if review.user != request.user:
            return Response(
                {'error': 'У вас нет прав на редактирование этого отзыва'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductReviewSerializer(review, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Частично обновить отзыв",
        request_body=ProductReviewSerializer,
        responses={200: ProductReviewSerializer()}
    )
    def patch(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        
        # Проверка прав доступа
        if review.user != request.user:
            return Response(
                {'error': 'У вас нет прав на редактирование этого отзыва'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Удалить отзыв",
        responses={204: 'Отзыв удален'}
    )
    def delete(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        
        # Проверка прав доступа
        if review.user != request.user:
            return Response(
                {'error': 'У вас нет прав на удаление этого отзыва'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)