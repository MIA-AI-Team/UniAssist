import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for the AI Evaluation Engine Service."""

    AI_ENGINE_VERSION: str = os.getenv("AI_ENGINE_VERSION", "1.4.0")
    PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "2.0.0")

    PRIMARY_PROVIDER: str = os.getenv("PRIMARY_PROVIDER", "groq").lower()

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "qwen/qwen3.8-27b")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")

    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))

    MAX_TOTAL_PROMPT_CHARS: int = int(os.getenv("MAX_TOTAL_PROMPT_CHARS", "48000"))
    BUDGET_REFERENCE_RATIO: float = float(os.getenv("BUDGET_REFERENCE_RATIO", "0.40"))
    BUDGET_RUBRIC_RATIO: float = float(os.getenv("BUDGET_RUBRIC_RATIO", "0.15"))
    BUDGET_SUBMISSION_RATIO: float = float(os.getenv("BUDGET_SUBMISSION_RATIO", "0.35"))
    BUDGET_CODE_RATIO: float = float(os.getenv("BUDGET_CODE_RATIO", "0.10"))

    MAX_REFERENCE_CHARS: int = int(os.getenv("MAX_REFERENCE_CHARS", "12000"))
    MAX_SUBMISSION_CHARS: int = int(os.getenv("MAX_SUBMISSION_CHARS", "12000"))
    MAX_CODE_FILE_CHARS: int = int(os.getenv("MAX_CODE_FILE_CHARS", "8000"))
    MAX_GRADING_KEY_CHARS: int = int(os.getenv("MAX_GRADING_KEY_CHARS", "6000"))

    MIN_RUBRIC_CRITERIA: int = int(os.getenv("MIN_RUBRIC_CRITERIA", "1"))
    MAX_RUBRIC_CRITERIA: int = int(os.getenv("MAX_RUBRIC_CRITERIA", "20"))
