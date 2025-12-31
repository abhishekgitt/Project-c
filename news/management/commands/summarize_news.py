import requests
import os
from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import SummaryPage

# Ollama config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

REQUEST_TIMEOUT = 300
# Number of database rows loaded into memory at a time
CHUNK_SIZE = int(os.getenv("AI_SUMMARY_DB_CHUNK_SIZE", 3))


def word_count(text: str) -> int:
    """Return number of words in text"""
    return len(text.split()) if text else 0


def build_prompt(text: str) -> str:
    """
    Strict structured prompt for geo-economic analysis.
    """
    return f"""
You are a senior economic and geopolitical analyst.

Summarize the news in this order and format.
Plain English only. Include bullet points at last.

Structure:
Explanation of the article in a simple words.
Don't tell how you going to explain it.
If news contains negative or positive effect on the economy explain which are the sectors may have effect.
Tell Estimated percentage impact on stocks and job market\\layoffs impact from this article.
How this news affects the country's economic growth (percentage estimate), Explain why and how country's economy will change.
What are the safer stocks to invest in the situation.

Rules:
No greetings
No next question recommendations
Can be longer
Keep simpler Explanation

News article:
{text}
"""


def generate_summary(text: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": build_prompt(text),
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()
    return (response.json().get("response") or "").strip()


class Command(BaseCommand):
    help = "Generate AI summaries using local LLM"

    def handle(self, *args, **options):
        self.stdout.write(" ---> Starting AI summarization...")

        pending_qs = SummaryPage.objects.filter(
            summarized_at__isnull=True
        ).select_related("article")

        if not pending_qs.exists():
            self.stdout.write(self.style.SUCCESS(" No pending articles."))
            return

        for summary_page in pending_qs.iterator(CHUNK_SIZE):
            article = summary_page.article
            text = (article.snippet or "").strip()

            # 🚫 Skip articles with less than 300 WORDS
            if word_count(text) < 300:
                self.stdout.write(
                    self.style.WARNING(
                        f" SKIPPED (short article, {word_count(text)} words): "
                        f"{article.title[:80]}"
                    )
                )
                # Do NOT save anything
                # Do NOT mark summarized_at
                continue

            try:
                self.stdout.write(f"{MODEL_NAME} --- Processing: {article.title[:80]}")

                ai_summary = generate_summary(text)

                if not ai_summary:
                    raise ValueError("Empty AI response")

                summary_page.ai_summary = ai_summary
                summary_page.summarized_at = timezone.now()
                summary_page.model_version = MODEL_NAME
                summary_page.confidence = 0.85
                summary_page.save()

                self.stdout.write(self.style.SUCCESS("✔ Summary saved"))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f" AI failed, skipping article: {str(e)}")
                )
                # ❌ Do NOT mark summarized_at
                # ❌ Do NOT save fallback summary
                continue

        self.stdout.write(self.style.SUCCESS("AI summarization completed."))
