import os


class LLMConfig:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    DEFAULT_MODEL = os.getenv('LLM_DEFAULT_MODEL', 'gemini-pro')
    MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '2048'))
    TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    HOST = os.getenv('LLM_HOST', '0.0.0.0')
    PORT = int(os.getenv('LLM_PORT', '8000'))
