from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from news.models import (
    SummaryPage,
    Topic,
)
from news.serializers import SummaryPageSerializer
from news.services.gemini import article_conversation



# sign up new user
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "username already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )



# Check userpreference (Now Global Feed)
class SummaryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Return ALL summaries, latest first
        summaries = SummaryPage.objects.select_related("article").order_by("-article__published_at")
        serializer = SummaryPageSerializer(summaries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Ask about article
class ArticleChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        article_id = request.data.get("article_id")
        summary_id = request.data.get("summary_id")
        user_question = request.data.get("question")

        if not article_id or not summary_id or not user_question:
            return Response(
                {"error": "article_id, summary_id and question are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            summary = SummaryPage.objects.select_related("article").get(
                id=summary_id
            )
        except SummaryPage.DoesNotExist:
            return Response(
                {"error": "Summary not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Removed Topic Permission Check - Allow any authenticated user to chat about any article

        article_text = summary.article.snippet or summary.article.title

        reply = article_conversation(
            article_text=article_text,
            user_question=user_question
        )

        return Response({"reply": reply}, status=status.HTTP_200_OK)