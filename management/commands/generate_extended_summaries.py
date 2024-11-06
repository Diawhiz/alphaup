# news/management/commands/generate_extended_summaries.py
from django.core.management.base import BaseCommand
from news.models import Article
from news.views import NewsService 

class Command(BaseCommand):
    help = 'Generate extended summaries for existing articles'

    def handle(self, *args, **options):
        articles = Article.objects.filter(extended_summary='')
        total = articles.count()
        
        self.stdout.write(f'Generating extended summaries for {total} articles...')
        
        for i, article in enumerate(articles, 1):
            try:
                extended_summary = NewsService.generate_extended_summary(
                    article.summary, 
                    ''  # No content available for existing articles
                )
                article.extended_summary = extended_summary
                article.save()
                self.stdout.write(f'Processed {i}/{total} articles')
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error processing article {article.id}: {str(e)}'
                ))
        
        self.stdout.write(self.style.SUCCESS('Successfully generated extended summaries'))