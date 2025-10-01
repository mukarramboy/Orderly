from django.urls import path
from .views import (
    # Категории
    CategoryListView,
    CategoryDetailView,
    RootCategoriesView,
    CategorySubcategoriesView,
    
    # Товары
    ProductListView,
    ProductDetailView,
    ProductByCategoryView,
    MyProductsView,
    ProductAddImageView,
    ProductAddReviewView,
    
    # Заказы
    OrderListView,
    OrderDetailView,
    OrderCancelView,
    OrderRefundView,
    OrderUpdateStatusView,
    
    # Отзывы
    ReviewListView,
    MyReviewsView,
    ReviewDetailView,
)


urlpatterns = [
    # ==================== КАТЕГОРИИ ====================
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categorie/detail/', CategoryDetailView.as_view(), name='')
]