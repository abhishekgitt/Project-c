from django.db import models

class Article(models.Model):
    source = models.CharField(max_length=200)
    title = models.TextField()
    url = models.URLField(unique=True)
    published_at = models.DateTimeField(null=True,blank=True)
    summary = models.TextField(blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.source} - {self.title[:60]}"