import logging
from groq import Groq
logger = logging.getLogger(__name__)

class Response:
    def __init__(self, api_key: str, model_name: str, encoder, system_prompt: str) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.encoder = encoder
        self.system_prompt = system_prompt
        try:
            self.client = Groq(api_key=self.api_key)
            logging.info("OpenAI client initialized.")
        except Exception as e:
            logging.critical("Failed to initialize OpenAI client as %s", e)
            self.client = None

    def generate_response(self, query: str, context: str) -> str:
        if self.client is None:
            return "Error: AI client not configured."
        prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=1,
                top_p=1,
                model=self.model_name,
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