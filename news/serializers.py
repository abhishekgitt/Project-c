# --- Json converstion ---
from rest_framework import serializers
from .models import Article, SummaryPage

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"

class SummaryPageSerializer(serializers.ModelSerializer):
    article = ArticleSerializer(read_only=True)

    class Meta:
        model = SummaryPage
        fields = "__all__"
