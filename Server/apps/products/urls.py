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
    path('categories/detail/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:category_id>/subcategories/', CategorySubcategoriesView.as_view(), name='category-subcategories'),
    path('categories/root/', RootCategoriesView.as_view(), name='root-categories'),
    path('categories/<int:category_id>/products/', ProductByCategoryView.as_view(), name='products-by-category'),
    path('products/my/', MyProductsView.as_view(), name='my-products'),
    path('products/<int:product_id>/add-image/', ProductAddImageView.as_view(), name='product-add-image'),
    path('products/<int:product_id>/add-review/', ProductAddReviewView.as_view(), name='product-add-review'),  
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/detail/', ProductDetailView.as_view(), name='product-detail'),       
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/detail/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<int:order_id>/refund/', OrderRefundView.as_view(), name='order-refund'),
    path('orders/<int:order_id>/update-status/', OrderUpdateStatusView.as_view(), name='order-update-status'),
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/my/', MyReviewsView.as_view(), name='my-reviews'),
    path('reviews/detail/', ReviewDetailView.as_view(), name='review-detail'),
]