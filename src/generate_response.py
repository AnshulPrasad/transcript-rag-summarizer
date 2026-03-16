import logging
from groq import Groq
import tiktoken

from src.tokenizer import count_tokens
from config import MODEL, GROQ_API_KEY, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

try:
    encoder = tiktoken.encoding_for_model(MODEL)
except KeyError:
    # fallback for custom or unrecognized model names
    encoder = tiktoken.get_encoding("cl100k_base")

try:
    client = Groq(api_key=GROQ_API_KEY)
    logging.info("OpenAI client initialized.")
except Exception as e:
    logging.critical("Failed to initialize OpenAI client as %s", e)
    client = None


def generate_response(query: str, context: str) -> str:

    if client is None:
        return "Error: AI client not configured."

    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    logging.info("Total number of tokens in prompt: %s", count_tokens(prompt))

    try:

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=1,
            top_p=1,
            model=MODEL,
            stream=False,
        )

        # Extract text defensively (depends on SDK return shape)
        try:
            response = response.choices[0].message.content
        except Exception as e:
            response = getattr(response, "text", None) or str(response)
            logging.warning("Fallback used for response parsing as %s", e)

        logging.info("Answer generation succeeded.")
        return response

    except Exception as e:
        logging.error("Error during API call as %s", e)
        return "Sorry, there was an error generating the response."
