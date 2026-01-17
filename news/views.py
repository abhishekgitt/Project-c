from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from news.models import (
    SummaryPage,
    Topic,
    UserPreference,
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

        # create EMPTY user preference (no default topics)
        UserPreference.objects.create(user=user)

        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )


# List Topics
class TopicListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        topics = Topic.objects.all()
        return Response([
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug
            }
            for t in topics
        ])



# Save UserPreferences
class SaveUserPreferencesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        topic_ids = request.data.get("topics", [])

        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        pref.preferred_topics.set(
            Topic.objects.filter(id__in=topic_ids)
        )

        return Response({"status": "saved"})



# Check userpreference
class SummaryListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            user_pref = user.userpreference
        except UserPreference.DoesNotExist:
            return Response(
                {"needs_onboarding": True, "summaries": []},
                status=status.HTTP_200_OK
            )

        topics = user_pref.preferred_topics.all()

        if not topics.exists():
            return Response(
                {"needs_onboarding": True, "summaries": []},
                status=status.HTTP_200_OK
            )

        summaries = SummaryPage.objects.filter(
            article__topics__in=topics
        ).select_related("article").distinct()

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

        user_topics = request.user.userpreference.preferred_topics.all()

        if not summary.article.topics.filter(
            id__in=user_topics.values_list("id", flat=True)
        ).exists():
            return Response(
                {"error": "You are not allowed to access this article"},
                status=status.HTTP_403_FORBIDDEN
            )

        article_text = summary.article.snippet or summary.article.title

        reply = article_conversation(
            article_text=article_text,
            user_question=user_question
        )

        return Response({"reply": reply}, status=status.HTTP_200_OK)