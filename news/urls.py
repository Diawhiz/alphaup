# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, CommentViewSet, fetch_news, news_list

router = DefaultRouter()
router.register(r'articles', ArticleViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = [
    path('', news_list, name='news-list'),
    path('api/', include(router.urls)),
    path('api/fetch-news/', fetch_news, name='fetch-news'),
]