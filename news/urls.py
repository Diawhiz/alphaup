from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet)
router.register(r'comments', views.CommentViewSet)

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('api/', include(router.urls)),
    path('fetch/', views.fetch_news, name='fetch_news'),
]