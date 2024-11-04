from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from .models import Article, Comment
from .serializers import ArticleSerializer, CommentSerializer
import requests
from django.conf import settings

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def get_queryset(self):
        queryset = Article.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by('-published_at')  # Add ordering

@api_view(['POST'])
def fetch_news(request):
    try:
        newsapi = NewsApiClient(api_key=settings.NEWS_API_KEY)  # Get API key from settings
        
        categories = ['general', 'technology', 'business', 'science', 'health', 'entertainment']
        articles_created = 0
        articles_failed = 0
        
        for category in categories:
            try:
                news = newsapi.get_top_headlines(
                    category=category,
                    language='en',
                    page_size=10
                )
                
                for article in news.get('articles', []):  # Safely get articles
                    try:
                        if not Article.objects.filter(url=article['url']).exists():
                            Article.objects.create(
                                title=article.get('title', ''),
                                url=article['url'],
                                source=article.get('source', {}).get('name', 'Unknown'),
                                category=category,
                                summary=article.get('description', ''),
                                published_at=article.get('publishedAt')
                            )
                            articles_created += 1
                    except Exception as e:
                        articles_failed += 1
                        
            except Exception as e:
                return Response({
                    'error': f'Error fetching {category} news: {str(e)}',
                    'status': 'error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response({
            'message': f'Successfully fetched {articles_created} new articles',
            'failed': articles_failed,
            'status': 'success'
        })
        
    except Exception as e:
        return Response({
            'error': f'NewsAPI configuration error: {str(e)}',
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        queryset = Comment.objects.all()
        article_id = self.request.query_params.get('article_id')
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        return queryset.order_by('-created_at')  # Assuming you have a created_at field
    
    def create(self, request, *args, **kwargs):
        article_id = request.data.get('article_id')
        content = request.data.get('content', '').strip()  # Strip whitespace
        username = request.data.get('username', 'Anonymous')
        
        if not content:
            return Response(
                {'error': 'Comment content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response(
                {'error': 'Article not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        comment = Comment.objects.create(
            article=article,
            content=content,
            username=username
        )
        
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)