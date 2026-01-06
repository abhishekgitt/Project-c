import requests
import os
from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import SummaryPage
from news.news_summarizer.llmrequest import generate_summary, MODEL_NAME


# Number of database rows loaded into memory at a time
CHUNK_SIZE = int(os.getenv("AI_SUMMARY_DB_CHUNK_SIZE", 3))




def word_count(text: str) -> int:
    """Return number of words in text"""
    # split() - split words in a list : and return the count 
    return len(text.split()) if text else 0



class Command(BaseCommand):
    help = "Generate AI summaries using local LLM"

    def handle(self, *args, **options):
        self.stdout.write(" ---> Starting AI summarization...")

        # Select those summarized_at column where __isnull, and select related article.
        pending_qs = SummaryPage.objects.filter(
            summarized_at__isnull=True
        ).select_related("article")

        # Check at least one article without ai summary exists, if not return
        if not pending_qs.exists():
            self.stdout.write(self.style.SUCCESS(" No pending articles."))
            return

        for summary_page in pending_qs.iterator(CHUNK_SIZE):
            article = summary_page.article
            text = (article.snippet or "").strip()

            # -----> Skip articles with less than 300 WORDS 
            if word_count(text) < 300:
                self.stdout.write(
                    self.style.WARNING(
                        f" SKIPPED (short article, {word_count(text)} words): "
                        f"{article.title[:80]}"
                    )
                )
                # summarized_at will not be get marked
                continue



            try:
                self.stdout.write(f"{MODEL_NAME} --- Processing: {article.title[:80]}")

                ai_summary = generate_summary(text)

                if not ai_summary:
                    raise ValueError("Empty AI response")
                #loopvar.field
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
                continue

        self.stdout.write(self.style.SUCCESS("AI summarization completed."))
