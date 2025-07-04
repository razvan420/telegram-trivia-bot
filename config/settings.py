"""
Configuration settings for the Quiz Bot
"""
import os
from pathlib import Path

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7906411405:AAH6emugd5kmTa1k3GjIwNfDElbJiTnRLG4")

# File paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
SCORES_FILE = DATA_DIR / "user_scores.json"

# Quiz Configuration
MAX_QUESTIONS_PER_QUIZ = 10
QUESTION_TIMEOUT = 15  # seconds
NEXT_QUESTION_DELAY = 20  # seconds

# Default settings
DEFAULT_LANGUAGE = "ro"
DEFAULT_SELECTION_STRATEGY = "weighted_random"

# Logging Configuration
LOGGING_CONFIG = {
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'level': 'INFO'
}

# Available selection strategies
SELECTION_STRATEGIES = [
    "weighted_random",
    "balanced_categories", 
    "difficulty_progression",
    "adaptive",
    "simple_random"
]

# Category files mapping
CATEGORY_FILES = {
    'ro': 'ro-questions.json'
}

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
QUESTIONS_DIR.mkdir(exist_ok=True)