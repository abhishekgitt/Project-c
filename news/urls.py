from django.urls import path
from news.views import (
    SummaryListAPIView,
    ArticleChatAPIView,
    RegisterAPIView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view(), name="token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/register/", RegisterAPIView.as_view()),

    path("api/summaries/", SummaryListAPIView.as_view(), name="summary-list"),
    path("api/chat/", ArticleChatAPIView.as_view()),
]
