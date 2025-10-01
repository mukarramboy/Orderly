from rest_framework import permissions


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Разрешение для продавцов: только чтение для всех, 
    запись только для продавцов
    """
    
    def has_permission(self, request, view):
        # Разрешаем безопасные методы (GET, HEAD, OPTIONS) для всех
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Для остальных методов требуется аутентификация и профиль продавца
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'seller_profile')
        )
    
    def has_object_permission(self, request, view, obj):
        # Разрешаем безопасные методы для всех
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Проверяем, что пользователь - владелец объекта
        return obj.seller == request.user.seller_profile


class IsOrderOwner(permissions.BasePermission):
    """
    Разрешение для владельцев заказов
    """
    
    def has_object_permission(self, request, view, obj):
        # Покупатель может управлять своими заказами
        if obj.buyer == request.user:
            return True
        
        # Продавец может управлять заказами со своими товарами
        if hasattr(request.user, 'seller_profile'):
            return obj.items.filter(
                product__seller=request.user.seller_profile
            ).exists()
        
        return False


class IsReviewOwner(permissions.BasePermission):
    """
    Разрешение для владельцев отзывов
    """
    
    def has_object_permission(self, request, view, obj):
        # Только владелец отзыва может его редактировать
        return obj.user == request.user