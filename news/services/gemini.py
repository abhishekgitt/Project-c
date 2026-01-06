import os
from google import genai
from google.genai.errors import ClientError

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Model fallback order (cheap → strong)
MODEL_PRIORITY = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash",
]

def article_conversation(article_text: str, user_question: str) -> str:

    prompt = f"""
    1. You are a professional, friendly economic analyst.
    2. Start conversation without introduction 
    3. Explalin topic without telling about how you are going to explain it 
    4. At the end of conversation recommend related topics about the news 

    Here is a news article:
    {article_text}

    User question:
    {user_question}

    Answer in a clear, calm and helpful way.
    """

    last_error = None

    for model in MODEL_PRIORITY:
        
        try:
            print(f"Trying Gemini model: {model}")

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            # Success 
            return response.text

        except ClientError as e:
            last_error = e
            error_msg = str(e).lower()

            print(f"Model failed: {model}")

            # Quota / To many request / rate   → try next model
            RETRY_ERRORS = ("quota","429","not found")

            if any(keyword in error_msg for keyword in RETRY_ERRORS):
                continue

            # Any other error → stop immediately
            raise

    # If all models fail
    raise RuntimeError("All Gemini models exhausted") from last_error
