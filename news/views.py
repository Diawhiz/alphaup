from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from .models import Article, Comment
from .serializers import ArticleSerializer, CommentSerializer

# Create your views here.
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def get_queryset(self):
        category = self.request.query_params.get('category', None)
        if category:
            return Article.objects.filter(category=category)
        return Article.objects.all()

@api_view(['POST'])
def fetch_news(request):
    newsapi = NewsApiClient(api_key='your-api-key')
    
    categories = ['general', 'technology', 'business', 'science', 'health', 'entertainment']
    articles_created = 0
    
    for category in categories:
        news = newsapi.get_top_headlines(
            category=category,
            language='en',
            page_size=10
        )
        
        for article in news['articles']:
            if not Article.objects.filter(url=article['url']).exists():
                Article.objects.create(
                    title=article['title'],
                    url=article['url'],
                    source=article['source']['name'],
                    category=category,
                    summary=article['description'] or '',
                    published_at=article['publishedAt']
                )
                articles_created += 1
    
    return Response({
        'message': f'Successfully fetched {articles_created} new articles',
        'status': 'success'
    })

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def create(self, request, *args, **kwargs):
        article_id = request.data.get('article_id')
        content = request.data.get('content')
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