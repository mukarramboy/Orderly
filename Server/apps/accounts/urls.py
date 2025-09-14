from django.urls import path
from . import views

urlpatterns = [
    path('register/stage1/', views.Stage1View.as_view(), name='stage1'),
    path('register/stage2/', views.Stage2View.as_view(), name='stage2'),
    path('register/stage3/', views.Stage3View.as_view(), name='stage3'),
    path('profile/stage4/<int:user_id>/', views.Stage4View.as_view(), name='stage4'),
]