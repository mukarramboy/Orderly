from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Настройка Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce API",
        default_version='v1',
        description="""
        # API документация для интернет-магазина
        
        ## Функциональность:
        - **Категории** - управление категориями товаров
        - **Товары** - CRUD операции с товарами, фильтрация, поиск
        - **Заказы** - создание и управление заказами
        - **Отзывы** - добавление и просмотр отзывов на товары
        
        ## Аутентификация:
        API поддерживает несколько методов аутентификации:
        - JWT токены (рекомендуется)
        - DRF Token
        - Session authentication
        
        ## Права доступа:
        - Просмотр товаров и категорий - все пользователи
        - Создание товаров - только продавцы
        - Создание заказов - только авторизованные покупатели
        - Управление заказами - владельцы заказов и продавцы
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/accounts/', include('apps.accounts.urls')),
    
    # Swagger/ReDoc URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # DRF browsable API auth
    path('api-auth/', include('rest_framework.urls'))
]