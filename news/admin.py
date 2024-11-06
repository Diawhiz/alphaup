from django.contrib import admin

from .models import Article, Comment

# Register your models here.

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'source', 'category', 'summary', 'published_at', 'author', 'country')
    list_filter = ['created_at']
    # search_fields = ('name', 'email', 'body')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'content', 'username', 'created_at')
    list_filter = ['created_at']
    # search_fields = ('name', 'email', 'body')