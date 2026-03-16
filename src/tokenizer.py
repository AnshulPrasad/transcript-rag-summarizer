class Tokenizer:
    def __init__(self, model_name: str, encoder):
        self.model_name = model_name
        self.encoder = encoder

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoder.encode(text))


    def trim_to_token_limit(self, text: str, max_tokens: int) -> str:
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.encoder.decode(tokens[:max_tokens])