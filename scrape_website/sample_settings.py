from pathlib import Path

import openai

cwd = str(Path(__file__).parent.absolute())
openai.api_key = ""
openai.organization = ""

PINECONE_API_KEY = ""
PINECONE_ENV = ""

COMPLETIONS_MODEL_v2 = "gpt-3.5-turbo"
COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"
PINECONE_EMBEDDING_MODEL = "text-similarity-babbage-001"

COMPLETIONS_API_PARAMS = {
    # We use temperature of 0.0 because it gives the most predictable, factual answer.
    "temperature": 0.0,
    "max_tokens": 300,
    "model": COMPLETIONS_MODEL,
}

COMPLETIONS_API_PARAMS_PERSONALISED = {
    # We use temperature of 0.0 because it gives the most predictable, factual answer.
    "temperature": 0.2,
    "max_tokens": 257,
    "model": COMPLETIONS_MODEL,
    "frequency_penalty": 0,
    "presence_penalty": 0.6,
    "stop": ["\nUSER:", "\nAI:"]
}

COMPLETIONS_API_INENT = {
    # We use temperature of 0.0 because it gives the most predictable, factual answer.
    "temperature": 0.0,
    "max_tokens": 60,
    "model": COMPLETIONS_MODEL,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

version = 2

messages_pattern = r"(\nUSER: |\nAI: )+"

DEBUG = True


class ScraperParams:
    URL = ""
    namespace = ""

    pinecone_index = ""

    max_depth = 20
    max_webpages = 10000
