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
CHUNK_SIZE = int(os.getenv("AI_SUMMARY_DB_CHUNK_SIZE",3))

def build_prompt(text: str) -> str:
    """
    Strict structured prompt for geo-economic analysis.
    """
    return f"""
You are a senior economic and geopolitical analyst.

Summarize the news STRICTLY in this order and format.
Plain English only. Bullet points only.

Structure:
- Main topic of the news
- How this affects the stock market
- Which stocks or sectors will be impacted
- Estimated percentage impact on stocks or sectors
- How this news affects the country's economic growth (percentage estimate)
- Safer stocks or defensive sectors during this situation

Rules:
- Be realistic with percentages
- Avoid speculation beyond reasonable estimates
- No markdown
- No greetings
- No extra explanations

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

            

        
            if len(text) < 300:
                self.stdout.write(
                    self.style.ERROR(
                        f" SKIPPED! (short content, {len(text)} chars): {article.title[:80]}"
                        )
                    )

                summary_page.ai_summary = (
                    "Main topic: Insufficient article content\n"
                    "- Stock market impact: Unable to determine\n"
                    "- Affected stocks/sectors: Not enough data\n"
                    "- Estimated impact: 0%\n"
                    "- Country growth impact: 0%\n"
                    "- Safer stocks: Large-cap defensive stocks"
                )
                summary_page.summarized_at = timezone.now()
                summary_page.model_version = MODEL_NAME
                summary_page.confidence = 0.2
                summary_page.save()
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
                summary_page.ai_summary = (
                    "Main topic: AI summarization failed\n"
                    "- Stock market impact: Unknown\n"
                    "- Affected stocks/sectors: Unknown\n"
                    "- Estimated impact: 0%\n"
                    "- Country growth impact: 0%\n"
                    "- Safer stocks: Gold, utilities, FMCG"
                )
                summary_page.summarized_at = timezone.now()
                summary_page.model_version = MODEL_NAME
                summary_page.confidence = 0.1
                summary_page.save()

                self.stdout.write(
                    self.style.ERROR(f"Failed: {str(e)}")
                )

        self.stdout.write(self.style.SUCCESS("AI summarization completed."))

