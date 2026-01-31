from django.db import models
from django.contrib.auth.models import User

# Topic of the articles
class Topic(models.Model):
    name = models.CharField(max_length=100,unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name




class Article(models.Model):
    source = models.CharField(max_length=200)
    title = models.TextField()
    url = models.URLField(unique=True)
    published_at = models.DateTimeField(null=True, blank=True)
    snippet = models.TextField(blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    topics = models.ManyToManyField(Topic,related_name="articles",blank=True)

class SummaryPage(models.Model):
    article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name="summary")
    hero_image = models.URLField(blank=True, default="/static/news/llama-logo.png")
    short_preview = models.TextField(blank=True)    # used on cards
    ai_summary = models.TextField(blank=True)       # detailed AI bullets
    summarized_at = models.DateTimeField(null=True, blank=True)
    model_version = models.CharField(max_length=64, blank=True)
    confidence = models.FloatField(null=True, blank=True)

class UserArticleInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    