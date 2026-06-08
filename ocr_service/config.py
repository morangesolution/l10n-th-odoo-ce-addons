from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_vision_model: str = "gpt-4o"
    ocr_timeout: int = 30
    scanned_text_threshold: int = 50  # chars; below this = treat as scanned
    # OpenRouter requires these; ignored by other providers
    llm_site_url: str = ""    # e.g. https://yourapp.com  (HTTP-Referer)
    llm_site_name: str = ""   # e.g. MyApp               (X-Title)
    # Set to false for providers that don't support json_object response_format
    # (e.g. some Ollama models). The system prompt still requests JSON output.
    llm_json_mode: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
