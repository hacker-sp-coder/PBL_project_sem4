from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'accounts', views.AccountViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'goals', views.GoalViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', views.register_user, name='register'),
    path('auth/login/', views.login_user, name='login'),
    path('reports/<int:user_id>/', views.financial_report, name='financial_report'),
    path('suggestions/<int:user_id>/', views.investment_suggestions, name='investment_suggestions'),
]