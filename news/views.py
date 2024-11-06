from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime
from .models import Article, Comment
from .serializers import ArticleSerializer, CommentSerializer
import requests
import logging
import nltk
from nltk.tokenize import sent_tokenize

# Set up logging
logger = logging.getLogger(__name__)

class ArticleViewSet(viewsets.ModelViewSet):
    """ViewSet for handling article operations"""
    queryset = Article.objects.all().order_by('-published_at')
    serializer_class = ArticleSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'summary', 'category', 'source']
    
    def get_queryset(self):
        """Custom queryset to support filtering"""
        queryset = Article.objects.all().order_by('-published_at')
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

try:
    nltk.download('punkt', quiet=True)
except:
    pass

class NewsService:
    """Service class to handle news-related operations"""
    
    @staticmethod
    def generate_extended_summary(description, content):
        """Generate an extended summary between 300-500 words"""
        try:
            # Combine description and content
            full_text = f"{description} {content}"
            
            # Tokenize into sentences
            sentences = sent_tokenize(full_text)
            
            # Initialize summary
            extended_summary = []
            word_count = 0
            
            # Add sentences until we reach desired length
            for sentence in sentences:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= 500:
                    extended_summary.append(sentence)
                    word_count += sentence_words
                if word_count >= 300:
                    break
            
            return ' '.join(extended_summary)
        except Exception as e:
            logging.error(f"Error generating extended summary: {str(e)}")
            return description  # Fallback to original description

    @staticmethod
    def create_article_from_data(article_data, category):
        """Create article from API data with extended summary"""
        try:
            # Generate extended summary
            description = article_data.get('description', '')
            content = article_data.get('content', '')  # Some APIs provide full content
            extended_summary = NewsService.generate_extended_summary(description, content)
            
            return Article.objects.create(
                title=article_data.get('title', ''),
                url=article_data.get('url', ''),
                source=article_data.get('source', 'Unknown'),
                category=category,
                summary=description,  # Keep original summary
                extended_summary=extended_summary,  # Add extended summary
                published_at=NewsService.parse_published_date(article_data.get('published_at')),
                author=article_data.get('author', ''),
                image=article_data.get('image', ''),
                country=article_data.get('country', '')
            )
        except Exception as e:
            logger.error(f"Error creating article: {str(e)}")
            raise

def news_list(request):
    """View to display list of news articles"""
    try:
        # Get category filter from query params
        category = request.GET.get('category', '')
        
        # Query articles
        articles = Article.objects.all().order_by('-published_at')
        if category:
            articles = articles.filter(category=category)
        
        # Get unique categories
        categories = Article.objects.values_list('category', flat=True).distinct()
        
        context = {
            'articles': articles,
            'categories': categories,
            'selected_category': category
        }
        
        return render(request, 'news/news_list.html', context)
    
    except Exception as e:
        logger.error(f"Error in news_list view: {str(e)}")
        messages.error(request, 'An error occurred while loading the news.')
        return render(request, 'news/news_list.html', {'articles': [], 'categories': []})

def article_detail(request, article_id):
    """View to display article details and handle comments"""
    try:
        article = get_object_or_404(Article, id=article_id)
        context = {
            'article': article,
        }
        return render(request, 'news/article_detail.html', context)
    except Exception as e:
        logger.error(f"Error in article_detail view: {str(e)}")
        messages.error(request, 'An error occurred while loading the article.')
        return redirect('news_list')

@api_view(['GET'])
def fetch_news(request):
    """View to fetch news from MediaStack API"""
    try:
        # Get API key
        api_key = NewsService.get_mediastack_api_key()
        
        # MediaStack API configuration
        base_url = "http://api.mediastack.com/v1/news"
        categories = [
            'general', 'business', 'technology', 'science', 
            'health', 'sports', 'entertainment'
        ]
        
        stats = {'created': 0, 'failed': 0}
        
        for category in categories:
            try:
                # Prepare API parameters
                params = {
                    'access_key': api_key,
                    'categories': category,
                    'languages': 'en',
                    'limit': 100,
                    'sort': 'published_desc'
                }
                
                # Make API request
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                
                news_data = response.json()
                
                if news_data.get('error'):
                    raise ValueError(f"API error: {news_data['error']['message']}")
                
                # Process articles
                for article_data in news_data.get('data', []):
                    try:
                        # Skip if article already exists
                        if not Article.objects.filter(url=article_data['url']).exists():
                            NewsService.create_article_from_data(article_data, category)
                            stats['created'] += 1
                    except Exception as e:
                        stats['failed'] += 1
                        logger.error(f"Error processing article: {str(e)}")
                
            except requests.RequestException as e:
                logger.error(f"API request error for {category}: {str(e)}")
                messages.warning(request, f"Error fetching {category} news: {str(e)}")
                continue
        
        # Log statistics
        logger.info(f"Articles created: {stats['created']}, failed: {stats['failed']}")
        
        if stats['created'] > 0:
            messages.success(request, f"Successfully fetched {stats['created']} new articles.")
        else:
            messages.info(request, "No new articles were found.")
            
        return redirect('news_list')
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        messages.error(request, str(e))
        return redirect('news_list')
        
    except Exception as e:
        logger.error(f"Unexpected error in fetch_news: {str(e)}")
        messages.error(request, 'An unexpected error occurred while fetching news.')
        return redirect('news_list')

class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for handling article comments"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """Filter comments by article_id if provided"""
        queryset = Comment.objects.all()
        article_id = self.request.query_params.get('article_id')
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new comment"""
        try:
            # Validate input
            article_id = request.data.get('article_id')
            content = request.data.get('content', '').strip()
            username = request.data.get('username', '').strip() or 'Anonymous'  # Default to 'Anonymous' if empty
            
            if not content:
                return Response(
                    {'error': 'Comment content is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get article
            try:
                article = Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                return Response(
                    {'error': 'Article not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create comment
            comment = Comment.objects.create(
                article=article,
                content=content,
                username=username
            )
            
            serializer = self.get_serializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating comment: {str(e)}")
            return Response(
                {'error': 'An error occurred while creating the comment'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )