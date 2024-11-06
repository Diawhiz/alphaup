from rest_framework import serializers
from .models import Article, Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'content', 'username', 'created_at']

class ArticleSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'url', 'source', 'category', 
                 'summary', 'published_at', 'author', 'image', 'country', 'comments']
        from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'url', 'source', 'category', 'summary', 
                 'published_at', 'author', 'image', 'country']
        read_only_fields = ['published_at']  # Protect published_at from direct modification
