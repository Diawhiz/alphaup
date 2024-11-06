from django.db import models
from django.utils import timezone

# Create your models here.
class Article(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    summary = models.TextField()
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=255, blank=True)
    image = models.URLField(max_length=500, blank=True)
    country = models.CharField(max_length=2, blank=True)
    
    class Meta:
        ordering = ['-published_at']
        
    def __str__(self):
        return self.title

class Comment(models.Model):
    article = models.ForeignKey(Article, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    username = models.CharField(max_length=50, default='Anonymous')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Comment by {self.username} on {self.article.title}"