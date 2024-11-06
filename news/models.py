from django.db import models
from django.utils import timezone

# Create your models here.
class Article(models.Model):
    title = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    source = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    summary = models.TextField()
    full_content = models.TextField(blank=True)  # New field for full article content
    published_at = models.DateTimeField()
    author = models.CharField(max_length=200, blank=True)
    image = models.URLField(blank=True)
    keywords = models.TextField(blank=True)  # New field for article keywords
    country = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['category']),
        ]

class Comment(models.Model):
    article = models.ForeignKey(Article, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    username = models.CharField(max_length=50, default='Anonymous')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Comment by {self.username} on {self.article.title}"