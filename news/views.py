from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from news.models import SummaryPage
from news.serializers import SummaryPageSerializer
from news.services.gemini import article_conversation


class SummaryListAPIView(APIView):
    def get(self, request):
        summaries = SummaryPage.objects.select_related("article").all()
        serializer = SummaryPageSerializer(summaries, many=True)  # Group of objects send through json (many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ArticleChatAPIView(APIView):
    def post(self, request):
        #Take these data from response
        article_id = request.data.get("article_id")
        summary_id = request.data.get("summary_id")
        user_question = request.data.get("question")

        #If one of the data is missing Response will be an error 
        if not article_id or not summary_id or not user_question:
            return Response(
                {"error": "article_id, summary_id and question are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Take article data of ai summary and send to gemini api 
            summary = SummaryPage.objects.select_related("article").get(id=summary_id)
        except SummaryPage.DoesNotExist:
            # if failed
            return Response(
                {"error": "Summary not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        # Take article content or it's title
        article_text =  summary.article.snippet or summary.article.title

        combined_context = f"""

        Full Article:
        {article_text}
        """

        reply = article_conversation(
            article_text=combined_context,
            user_question=user_question
        )

        return Response({"reply": reply}, status=status.HTTP_200_OK)