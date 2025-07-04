"""
Validation utilities for the Quiz Bot
"""
import re
from typing import Dict, List, Any, Optional

def validate_bot_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        return False
    
    # Basic token format validation (should be like: 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
    token_pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(token_pattern, token))

def validate_question_data(question_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate question data structure
    Returns (is_valid, error_message)
    """
    required_fields = ['question', 'options', 'correct_answer']
    
    # Check required fields
    for field in required_fields:
        if field not in question_data:
            return False, f"Missing required field: {field}"
    
    # Validate question text
    if not isinstance(question_data['question'], str) or not question_data['question'].strip():
        return False, "Question text must be a non-empty string"
    
    # Validate options
    options = question_data['options']
    if not isinstance(options, list):
        return False, "Options must be a list"
    
    if len(options) < 2:
        return False, "Must have at least 2 options"
    
    if len(options) > 10:
        return False, "Cannot have more than 10 options"
    
    for i, option in enumerate(options):
        if not isinstance(option, str) or not option.strip():
            return False, f"Option {i+1} must be a non-empty string"
    
    # Validate correct answer
    try:
        correct_answer = int(question_data['correct_answer'])
        if not 0 <= correct_answer < len(options):
            return False, f"Correct answer index {correct_answer} is out of range (0-{len(options)-1})"
    except (ValueError, TypeError):
        return False, "Correct answer must be a valid integer"
    
    # Validate optional fields
    if 'difficulty' in question_data:
        difficulty = question_data['difficulty']
        valid_difficulties = ['easy', 'medium', 'hard']
        if difficulty not in valid_difficulties:
            return False, f"Difficulty must be one of: {', '.join(valid_difficulties)}"
    
    if 'category' in question_data:
        category = question_data['category']
        if not isinstance(category, str) or not category.strip():
            return False, "Category must be a non-empty string"
    
    if 'explanation' in question_data:
        explanation = question_data['explanation']
        if explanation is not None and not isinstance(explanation, str):
            return False, "Explanation must be a string or null"
    
    return True, ""

def validate_user_data(user_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate user score data structure
    Returns (is_valid, error_message)
    """
    required_fields = ['user_id', 'username']
    
    # Check required fields
    for field in required_fields:
        if field not in user_data:
            return False, f"Missing required field: {field}"
    
    # Validate user_id
    try:
        user_id = int(user_data['user_id'])
        if user_id <= 0:
            return False, "User ID must be a positive integer"
    except (ValueError, TypeError):
        return False, "User ID must be a valid integer"
    
    # Validate username
    username = user_data['username']
    if not isinstance(username, str) or not username.strip():
        return False, "Username must be a non-empty string"
    
    # Validate numeric fields
    numeric_fields = ['total_score', 'questions_answered', 'correct_answers']
    for field in numeric_fields:
        if field in user_data:
            try:
                value = int(user_data[field])
                if value < 0:
                    return False, f"{field} must be non-negative"
            except (ValueError, TypeError):
                return False, f"{field} must be a valid integer"
    
    # Validate consistency
    if 'questions_answered' in user_data and 'correct_answers' in user_data:
        questions_answered = int(user_data['questions_answered'])
        correct_answers = int(user_data['correct_answers'])
        if correct_answers > questions_answered:
            return False, "Correct answers cannot exceed questions answered"
    
    # Validate language
    if 'preferred_language' in user_data:
        language = user_data['preferred_language']
        valid_languages = ['ro', 'en']  # Add more as needed
        if language not in valid_languages:
            return False, f"Language must be one of: {', '.join(valid_languages)}"
    
    return True, ""

def validate_chat_id(chat_id: Any) -> bool:
    """Validate chat ID"""
    try:
        chat_id = int(chat_id)
        # Telegram chat IDs can be negative for groups/channels
        return chat_id != 0
    except (ValueError, TypeError):
        return False

def validate_user_id(user_id: Any) -> bool:
    """Validate user ID"""
    try:
        user_id = int(user_id)
        # Telegram user IDs are always positive
        return user_id > 0
    except (ValueError, TypeError):
        return False

def validate_selection_strategy(strategy: str) -> bool:
    """Validate selection strategy"""
    valid_strategies = [
        "weighted_random",
        "balanced_categories", 
        "difficulty_progression",
        "adaptive",
        "simple_random"
    ]
    return strategy in valid_strategies

def validate_quiz_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate quiz configuration
    Returns (is_valid, error_message)
    """
    # Validate max questions
    if 'max_questions' in config:
        try:
            max_q = int(config['max_questions'])
            if not 1 <= max_q <= 50:
                return False, "Max questions must be between 1 and 50"
        except (ValueError, TypeError):
            return False, "Max questions must be a valid integer"
    
    # Validate timeout
    if 'question_timeout' in config:
        try:
            timeout = int(config['question_timeout'])
            if not 5 <= timeout <= 300:
                return False, "Question timeout must be between 5 and 300 seconds"
        except (ValueError, TypeError):
            return False, "Question timeout must be a valid integer"
    
    # Validate delay
    if 'next_question_delay' in config:
        try:
            delay = int(config['next_question_delay'])
            if not 5 <= delay <= 120:
                return False, "Next question delay must be between 5 and 120 seconds"
        except (ValueError, TypeError):
            return False, "Next question delay must be a valid integer"
    
    return True, ""

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input"""
    if not isinstance(text, str):
        return ""
    
    # Remove control characters and trim
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text).strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text

def validate_file_path(file_path: str) -> bool:
    """Validate file path"""
    if not isinstance(file_path, str):
        return False
    
    # Check for directory traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        return False
    
    # Check file extension
    allowed_extensions = ['.json', '.txt', '.csv']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        return False
    
    return True

def validate_json_structure(data: Any, expected_type: type) -> bool:
    """Validate JSON data structure"""
    if not isinstance(data, expected_type):
        return False
    
    if expected_type == list:
        # For question lists, check if all items are dictionaries
        return all(isinstance(item, dict) for item in data)
    elif expected_type == dict:
        # For user scores, check if all keys can be converted to integers
        try:
            for key in data.keys():
                int(key)
            return True
        except (ValueError, TypeError):
            return False
    
    return True

def validate_performance_data(performance: Dict[str, float]) -> bool:
    """Validate performance data structure"""
    if not isinstance(performance, dict):
        return False
    
    valid_difficulties = ['easy', 'medium', 'hard']
    
    for difficulty, value in performance.items():
        if difficulty not in valid_difficulties:
            return False
        
        if not isinstance(value, (int, float)):
            return False
        
        if not 0.0 <= value <= 1.0:
            return False
    
    return True

def validate_quiz_results(results: Dict[str, Any]) -> bool:
    """Validate quiz results structure"""
    if not isinstance(results, dict):
        return False
    
    required_fields = ['participants', 'total_participants']
    for field in required_fields:
        if field not in results:
            return False
    
    # Validate participants
    participants = results['participants']
    if not isinstance(participants, list):
        return False
    
    # Validate total participants
    try:
        total = int(results['total_participants'])
        if total < 0:
            return False
    except (ValueError, TypeError):
        return False
    
    return True