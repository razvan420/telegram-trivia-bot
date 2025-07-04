"""
Data service for loading and saving quiz data
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from models.quiz_question import QuizQuestion
from models.user_score import UserScore
from config.settings import QUESTIONS_DIR, SCORES_FILE, CATEGORY_FILES

logger = logging.getLogger(__name__)

class DataService:
    """Service for handling data loading and saving operations"""
    
    def __init__(self):
        self.user_scores: Dict[int, UserScore] = {}
        self.questions: List[QuizQuestion] = []
        
    def load_questions(self, language: str = "ro") -> List[QuizQuestion]:
        """Load questions from JSON files"""
        questions = []
        
        if language not in CATEGORY_FILES:
            logger.warning(f"Language {language} not supported, falling back to 'ro'")
            language = "ro"
        
        file_path = QUESTIONS_DIR / CATEGORY_FILES[language]
        
        try:
            if not file_path.exists():
                logger.error(f"Questions file not found: {file_path}")
                return questions
            
            with open(file_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            for i, q_data in enumerate(questions_data):
                try:
                    question = QuizQuestion.from_dict(q_data)
                    questions.append(question)
                except Exception as e:
                    logger.error(f"Error parsing question {i+1}: {e}")
                    continue
            
            logger.info(f"Loaded {len(questions)} questions for language '{language}'")
            
        except Exception as e:
            logger.error(f"Error loading questions from {file_path}: {e}")
        
        self.questions = questions
        return questions
    
    def load_user_scores(self) -> Dict[int, UserScore]:
        """Load user scores from JSON file"""
        try:
            if SCORES_FILE.exists():
                with open(SCORES_FILE, 'r', encoding='utf-8') as f:
                    scores_data = json.load(f)
                
                self.user_scores = {
                    int(uid): UserScore.from_dict(data) 
                    for uid, data in scores_data.items()
                }
                
                logger.info(f"Loaded scores for {len(self.user_scores)} users")
            else:
                logger.info("No existing scores file found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading user scores: {e}")
            self.user_scores = {}
        
        return self.user_scores
    
    def save_user_scores(self, user_scores: Dict[int, UserScore]) -> bool:
        """Save user scores to JSON file with atomic write and backup"""
        try:
            # Convert to serializable format
            scores_data = {str(uid): score.to_dict() for uid, score in user_scores.items()}
            
            # Write to temporary file first
            temp_path = SCORES_FILE.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(scores_data, f, indent=2, ensure_ascii=False)
            
            # Create backup if original exists
            if SCORES_FILE.exists():
                backup_path = SCORES_FILE.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.unlink()
                SCORES_FILE.rename(backup_path)
            
            # Move temp file to final location
            temp_path.rename(SCORES_FILE)
            
            logger.info(f"Successfully saved scores for {len(user_scores)} users")
            return True
            
        except Exception as e:
            logger.error(f"Critical save error: {e}")
            
            # Attempt to restore from backup
            backup_path = SCORES_FILE.with_suffix('.bak')
            if 'backup_path' in locals() and backup_path.exists():
                try:
                    backup_path.rename(SCORES_FILE)
                    logger.info("Restored scores from backup")
                except Exception as restore_error:
                    logger.critical(f"Failed to restore backup: {restore_error}")
            
            return False
    
    def get_user_score(self, user_id: int, username: str) -> UserScore:
        """Get or create user score"""
        if user_id not in self.user_scores:
            self.user_scores[user_id] = UserScore(
                user_id=user_id,
                username=username
            )
        else:
            # Update username if it changed
            self.user_scores[user_id].username = username
        
        return self.user_scores[user_id]
    
    def validate_question_data(self, q_data: dict) -> bool:
        """Validate question structure"""
        required_fields = ['question', 'options', 'correct_answer']
        
        if not all(field in q_data for field in required_fields):
            return False
        
        if not isinstance(q_data['options'], list) or len(q_data['options']) < 2:
            return False
        
        try:
            correct_idx = int(q_data['correct_answer'])
            if not 0 <= correct_idx < len(q_data['options']):
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def get_question_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded questions"""
        if not self.questions:
            return {}
        
        stats = {
            'total_questions': len(self.questions),
            'by_category': {},
            'by_difficulty': {}
        }
        
        for question in self.questions:
            # Count by category
            category = question.category
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count by difficulty
            difficulty = question.difficulty
            stats['by_difficulty'][difficulty] = stats['by_difficulty'].get(difficulty, 0) + 1
        
        return stats