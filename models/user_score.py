"""
UserScore data model
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any

@dataclass
class UserScore:
    """Data class for user scores"""
    user_id: int
    username: str
    total_score: int = 0
    questions_answered: int = 0
    correct_answers: int = 0
    last_activity: str = ""
    preferred_language: str = "ro"
    
    def __post_init__(self):
        """Set default last_activity if not provided"""
        if not self.last_activity:
            self.last_activity = datetime.now().isoformat()
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.questions_answered) * 100
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now().isoformat()
    
    def add_answer(self, is_correct: bool, points: int = 1):
        """Add a new answer and update statistics"""
        self.questions_answered += 1
        if is_correct:
            self.correct_answers += 1
            self.total_score += points
        self.update_activity()
    
    def get_last_activity_date(self) -> str:
        """Get formatted last activity date"""
        try:
            dt = datetime.fromisoformat(self.last_activity)
            return dt.strftime("%Y-%m-%d")
        except:
            return "Niciodată"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserScore':
        """Create UserScore from dictionary"""
        return cls(**data)
    
    def get_performance_by_difficulty(self, performance_data: Dict[str, list]) -> Dict[str, float]:
        """Calculate performance by difficulty level"""
        performance = {}
        for difficulty in ["easy", "medium", "hard"]:
            if difficulty in performance_data and performance_data[difficulty]:
                correct_count = sum(performance_data[difficulty])
                total_count = len(performance_data[difficulty])
                performance[difficulty] = correct_count / total_count
            else:
                performance[difficulty] = 0.5  # Default neutral performance
        return performance