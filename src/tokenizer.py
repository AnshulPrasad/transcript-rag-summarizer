import tiktoken
from config import MODEL


# Limit the length of combined transcripts for ChatGPT ready
try:
    encoder = tiktoken.encoding_for_model(MODEL)
except KeyError:
    # fallback for custom or unrecognized model names
    encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Return the number of tokens in a string, using your model's tokenizer."""
    if not text:
        return 0
    return len(encoder.encode(text))


def trim_to_token_limit(text: str, max_tokens: int) -> str:
    """
    If text exceeds max_tokens, cut it down to the first max_tokens tokens.
    """
    tokens = encoder.encode(text)
    if len(tokens) <= max_tokens:
        return text
    # decode only the first max_tokens tokens back into a string
    return encoder.decode(tokens[:max_tokens])
