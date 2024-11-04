from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime, timedelta
from .models import Article, Comment
from .serializers import ArticleSerializer, CommentSerializer
import requests
from django.conf import settings

def news_list(request):
    category = request.GET.get('category', '')
    
    articles = Article.objects.all().order_by('-published_at')
    if category:
        articles = articles.filter(category=category)
    
    categories = Article.objects.values_list('category', flat=True).distinct()
    
    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': category
    }
    
    return render(request, 'news/news_list.html', context)

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def get_queryset(self):
        queryset = Article.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by('-published_at')

@api_view(['GET', 'POST'])
def fetch_news(request):
    if request.method == 'GET':
        return news_list(request)

    try:
        # Mediastack API endpoint
        base_url = "http://api.mediastack.com/v1/news"
        
        # Categories in Mediastack
        categories = [
            'general', 'business', 'technology', 'science', 
            'health', 'sports', 'entertainment'
        ]
        
        articles_created = 0
        articles_failed = 0
        
        for category in categories:
            try:
                # Mediastack API parameters
                params = {
                    'access_key': settings.MEDIASTACK_API_KEY,
                    'categories': category,
                    'languages': 'en',
                    'limit': 10,
                    'sort': 'published_desc'  # Get latest news first
                }
                
                response = requests.get(base_url, params=params)
                if response.status_code != 200:
                    raise Exception(f"API returned status code {response.status_code}")
                
                news_data = response.json()
                
                if news_data.get('error'):
                    raise Exception(f"API error: {news_data['error']['message']}")
                
                for article in news_data.get('data', []):
                    try:
                        # Check if article already exists using URL
                        if not Article.objects.filter(url=article['url']).exists():
                            # Convert Mediastack datetime string to Python datetime
                            published_at = datetime.strptime(
                                article['published_at'], 
                                '%Y-%m-%dT%H:%M:%S%z'
                            )
                            
                            Article.objects.create(
                                title=article.get('title', ''),
                                url=article.get('url', ''),
                                source=article.get('source', 'Unknown'),
                                category=category,
                                summary=article.get('description', ''),
                                published_at=published_at,
                                # Additional Mediastack-specific fields you might want to add:
                                # author=article.get('author', ''),
                                # image=article.get('image', ''),
                                # country=article.get('country', '')
                            )
                            articles_created += 1
                    except Exception as e:
                        articles_failed += 1
                        print(f"Error creating article: {str(e)}")  # For debugging
                        
            except Exception as e:
                return Response({
                    'error': f'Error fetching {category} news: {str(e)}',
                    'status': 'error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # After successful fetch, redirect to template view
        return news_list(request)
        
    except Exception as e:
        return Response({
            'error': f'Mediastack API configuration error: {str(e)}',
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
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        article_id = request.data.get('article_id')
        content = request.data.get('content', '').strip()
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