"""
Helper utilities for the Quiz Bot
"""
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """Format duration between two timestamps"""
    if end_time is None:
        end_time = datetime.now()
    
    duration = end_time - start_time
    
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} secunde"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal as percentage"""
    try:
        percentage = value * 100
        return f"{percentage:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0.0%"

def format_number(number: int) -> str:
    """Format large numbers with appropriate suffixes"""
    if number < 1000:
        return str(number)
    elif number < 1_000_000:
        return f"{number/1000:.1f}K"
    elif number < 1_000_000_000:
        return f"{number/1_000_000:.1f}M"
    else:
        return f"{number/1_000_000_000:.1f}B"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters"""
    import re
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250 - len(ext)] + ('.' + ext if ext else '')
    return filename

def parse_iso_datetime(iso_string: str) -> Optional[datetime]:
    """Parse ISO datetime string safely"""
    try:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def get_relative_time(target_time: datetime, reference_time: Optional[datetime] = None) -> str:
    """Get relative time description (e.g., '2 hours ago', 'in 3 minutes')"""
    if reference_time is None:
        reference_time = datetime.now()
    
    # Ensure both times have the same timezone info
    if target_time.tzinfo != reference_time.tzinfo:
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=reference_time.tzinfo)
        elif reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=target_time.tzinfo)
    
    delta = target_time - reference_time
    total_seconds = delta.total_seconds()
    
    if abs(total_seconds) < 60:
        return "acum"
    
    is_future = total_seconds > 0
    total_seconds = abs(total_seconds)
    
    if total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds // 60)
        unit = "minut" if minutes == 1 else "minute"
        time_str = f"{minutes} {unit}"
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds // 3600)
        unit = "oră" if hours == 1 else "ore"
        time_str = f"{hours} {unit}"
    elif total_seconds < 2592000:  # Less than 30 days
        days = int(total_seconds // 86400)
        unit = "zi" if days == 1 else "zile"
        time_str = f"{days} {unit}"
    else:
        months = int(total_seconds // 2592000)
        unit = "lună" if months == 1 else "luni"
        time_str = f"{months} {unit}"
    
    return f"în {time_str}" if is_future else f"acum {time_str}"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def safe_json_load(file_path: Path, default: Any = None) -> Any:
    """Safely load JSON file with error handling"""
    try:
        if not file_path.exists():
            return default
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default

def safe_json_save(data: Any, file_path: Path, backup: bool = True) -> bool:
    """Safely save data to JSON file with optional backup"""
    try:
        # Create backup if requested and file exists
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(f'.bak')
            if backup_path.exists():
                backup_path.unlink()
            file_path.rename(backup_path)
        
        # Write to temporary file first
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Move temp file to final location
        temp_path.rename(file_path)
        return True
        
    except (IOError, json.JSONEncodeError) as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def calculate_accuracy(correct: int, total: int) -> float:
    """Calculate accuracy percentage"""
    if total == 0:
        return 0.0
    return (correct / total) * 100

def get_medal_emoji(position: int) -> str:
    """Get medal emoji for leaderboard positions"""
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    return medals.get(position, f"{position}.")

def format_leaderboard_entry(position: int, username: str, score: int, accuracy: float) -> str:
    """Format a single leaderboard entry"""
    medal = get_medal_emoji(position)
    return f"{medal} **{username}** - {score} pct ({accuracy:.1f}%)"

def validate_and_clean_username(username: str) -> str:
    """Validate and clean username"""
    if not username or not isinstance(username, str):
        return "Unknown"
    
    # Remove problematic characters
    import re
    username = re.sub(r'[^\w\s-_.]', '', username.strip())
    
    # Limit length
    if len(username) > 50:
        username = username[:47] + "..."
    
    return username or "Unknown"

def get_difficulty_emoji(difficulty: str) -> str:
    """Get emoji for difficulty level"""
    emojis = {
        "easy": "🟢",
        "medium": "🟡", 
        "hard": "🔴"
    }
    return emojis.get(difficulty.lower(), "⚪")

def get_category_emoji(category: str) -> str:
    """Get emoji for question category"""
    emojis = {
        "geografie": "🌍",
        "istorie": "📚",
        "stiinta": "🔬",
        "literatura": "📖",
        "arte": "🎨",
        "general": "🎯",
        "stiinte-natura": "🌿"
    }
    return emojis.get(category.lower(), "❓")

def format_quiz_question_text(question_number: int, total_questions: int, question_text: str) -> str:
    """Format quiz question with numbering"""
    return f"🎯 **Întrebarea #{question_number}/{total_questions}**\n\n{question_text}"

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Create a text-based progress bar"""
    if total == 0:
        return "▱" * length
    
    filled = int((current / total) * length)
    empty = length - filled
    
    return "▰" * filled + "▱" * empty

def format_quiz_stats(stats: Dict[str, Any]) -> str:
    """Format quiz statistics for display"""
    lines = []
    
    if 'total_questions' in stats:
        lines.append(f"📊 Total întrebări: {stats['total_questions']}")
    
    if 'by_category' in stats:
        lines.append("📚 Pe categorii:")
        for category, count in stats['by_category'].items():
            emoji = get_category_emoji(category)
            category_name = category.replace('-', ' ').title()
            lines.append(f"  {emoji} {category_name}: {count}")
    
    if 'by_difficulty' in stats:
        lines.append("🎯 Pe dificultate:")
        for difficulty, count in stats['by_difficulty'].items():
            emoji = get_difficulty_emoji(difficulty)
            lines.append(f"  {emoji} {difficulty.title()}: {count}")
    
    return "\n".join(lines)

def rate_limit_key(user_id: int, action: str) -> str:
    """Generate rate limit key for user actions"""
    return f"rate_limit:{user_id}:{action}"

def is_rate_limited(user_id: int, action: str, limit: int = 5, window: int = 60) -> bool:
    """Simple in-memory rate limiting (you might want to use Redis for production)"""
    # This is a simplified implementation
    # In production, you'd want to use a proper rate limiting solution
    current_time = datetime.now()
    
    # For now, just return False (no rate limiting)
    # You can implement proper rate limiting here
    return False

def sanitize_poll_options(options: List[str]) -> List[str]:
    """Sanitize poll options"""
    sanitized = []
    for option in options:
        if isinstance(option, str):
            # Clean and limit length
            clean_option = option.strip()[:100]
            if clean_option:
                sanitized.append(clean_option)
    
    return sanitized

def calculate_quiz_difficulty_score(questions: List[Any]) -> float:
    """Calculate overall difficulty score for a set of questions"""
    if not questions:
        return 0.0
    
    difficulty_weights = {"easy": 1, "medium": 2, "hard": 3}
    total_weight = 0
    
    for question in questions:
        difficulty = getattr(question, 'difficulty', 'medium')
        total_weight += difficulty_weights.get(difficulty, 2)
    
    # Normalize to 0-1 scale
    max_possible = len(questions) * 3
    return total_weight / max_possible if max_possible > 0 else 0.0

def get_performance_description(accuracy: float) -> str:
    """Get performance description based on accuracy"""
    if accuracy >= 90:
        return "🌟 Excelent"
    elif accuracy >= 75:
        return "🎯 Foarte bun"
    elif accuracy >= 60:
        return "👍 Bun"
    elif accuracy >= 40:
        return "📈 Mediocru"
    else:
        return "📉 Necesită îmbunătățire"

async def safe_delete_message(bot, chat_id: int, message_id: int) -> bool:
    """Safely delete a message with error handling"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except Exception as e:
        logger.warning(f"Could not delete message {message_id} in chat {chat_id}: {e}")
        return False

async def safe_edit_message(bot, chat_id: int, message_id: int, text: str, **kwargs) -> bool:
    """Safely edit a message with error handling"""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            **kwargs
        )
        return True
    except Exception as e:
        logger.warning(f"Could not edit message {message_id} in chat {chat_id}: {e}")
        return False

def create_backup_filename(original_path: Path) -> Path:
    """Create a backup filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return original_path.with_name(f"{original_path.stem}_{timestamp}{original_path.suffix}")

def cleanup_old_backups(directory: Path, pattern: str = "*.bak", keep_count: int = 5):
    """Clean up old backup files, keeping only the most recent ones"""
    try:
        backup_files = list(directory.glob(pattern))
        if len(backup_files) <= keep_count:
            return
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Remove old backups
        for old_backup in backup_files[keep_count:]:
            old_backup.unlink()
            logger.info(f"Cleaned up old backup: {old_backup}")
            
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")

def measure_execution_time(func_name: str = ""):
    """Decorator to measure function execution time"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = datetime.now() - start_time
                logger.debug(f"Function {func_name or func.__name__} took {execution_time.total_seconds():.3f}s")
        
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = datetime.now() - start_time
                logger.debug(f"Function {func_name or func.__name__} took {execution_time.total_seconds():.3f}s")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def generate_quiz_id() -> str:
    """Generate a unique quiz ID"""
    import uuid
    return str(uuid.uuid4())[:8]

def validate_telegram_entities(text: str) -> bool:
    """Validate that text doesn't contain problematic Telegram entities"""
    # Check for excessively long text
    if len(text) > 4096:
        return False
    
    # Check for problematic patterns
    problematic_patterns = [
        r'@channel',
        r'@everyone',
        r'@here',
    ]
    
    import re
    for pattern in problematic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True