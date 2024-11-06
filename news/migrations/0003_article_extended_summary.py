# Generated by Django 5.1.2 on 2024-11-06 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_article_author_article_country_article_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='extended_summary',
            field=models.TextField(blank=True, help_text='A comprehensive summary between 300-500 words'),
        ),
    ]