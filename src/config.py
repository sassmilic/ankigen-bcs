import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file in the project root
# Assumes config.py is in 'src/' and .env is in the parent directory.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- API Keys ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- File Paths ---
# Project root is the directory containing 'src/' and '.env'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Default directory for output files (CSV, logs, history)
# Can be overridden by command-line arguments for CSV output specifically
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Default input words file
DEFAULT_WORDS_FILE = os.path.join(PROJECT_ROOT, "words.txt")

# Path for the flashcard history file
HISTORY_FILE_PATH = os.path.join(DEFAULT_OUTPUT_DIR, "flashcard_history.jsonl")

# Path for the log file
LOG_FILE_PATH = os.path.join(DEFAULT_OUTPUT_DIR, "flashcard_generator.log")

# Path to Anki collection.media folder (user must set this in .env)
ANKI_COLLECTION_FILE_PATH = os.path.expanduser(os.environ.get("ANKI_COLLECTION_FILE_PATH", ""))

# --- OpenAI API Parameters ---
GPT_MODEL = "gpt-4-turbo"
GPT_TEMPERATURE = 0.4
IMAGE_GENERATION_MODEL = "gpt-image-1" # Model used in your script
IMAGE_SIZE = "1024x1024"
IMAGE_QUALITY = "low" # Quality used in your script for IMAGE_GENERATION_MODEL

# --- Rate Limiting & Delays ---
IMAGE_API_RATE_LIMIT = 20  # images per minute (as per your original comment)
IMAGE_API_RATE_PERIOD = 60  # seconds
API_RETRY_DELAY = 30  # seconds
INTER_BATCH_DELAY = 3  # seconds

# --- Batch Processing ---
DEFAULT_BATCH_SIZE = 10

# --- Logging ---
LOG_LEVEL = "INFO"  # e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL

# --- CSV Output Configuration ---
CSV_SEPARATOR = '\t'
CSV_HTML_ENABLED = True
CSV_NOTETYPE_COLUMN = '1' # Corresponds to Anki import settings for notetype 