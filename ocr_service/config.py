from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_vision_model: str = "gpt-4o"
    ocr_timeout: int = 30
    scanned_text_threshold: int = 50  # chars; below this = treat as scanned

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
