"""
QuizQuestion data model
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class QuizQuestion:
    """Data class for quiz questions"""
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    difficulty: str = "medium"
    category: str = "general"
    
    def __post_init__(self):
        """Validate question data after initialization"""
        if not isinstance(self.options, list) or len(self.options) < 2:
            raise ValueError("Question must have at least 2 options")
        
        if not (0 <= self.correct_answer < len(self.options)):
            raise ValueError("Correct answer index is out of range")
        
        if self.difficulty not in ["easy", "medium", "hard"]:
            self.difficulty = "medium"
    
    @property
    def correct_option(self) -> str:
        """Return the correct answer text"""
        return self.options[self.correct_answer]
    
    def is_correct(self, answer_index: int) -> bool:
        """Check if the given answer index is correct"""
        return answer_index == self.correct_answer
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'question': self.question,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'category': self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QuizQuestion':
        """Create QuizQuestion from dictionary"""
        return cls(
            question=data['question'],
            options=data['options'],
            correct_answer=data['correct_answer'],
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty', 'medium'),
            category=data.get('category', 'general')
        )