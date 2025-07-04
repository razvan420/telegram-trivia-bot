"""
Question selection service with multiple strategies
"""
import random
import math
import logging
from typing import List, Dict, Set, Optional
from collections import defaultdict

from models.quiz_question import QuizQuestion

logger = logging.getLogger(__name__)

class QuestionSelector:
    """Enhanced question selection with multiple strategies"""
    
    def __init__(self, questions: List[QuizQuestion]):
        self.questions = questions
        self.question_weights = defaultdict(float)
        self.user_question_history = defaultdict(set)  # user_id -> set of question indices
        self.global_question_usage = defaultdict(int)  # question_index -> usage_count
        self.category_distribution = self._analyze_categories()
        self.difficulty_distribution = self._analyze_difficulties()
        
        # Initialize weights
        self._initialize_weights()
        
        logger.info(f"QuestionSelector initialized with {len(questions)} questions")
    
    def _analyze_categories(self) -> Dict[str, List[int]]:
        """Analyze question distribution by category"""
        categories = defaultdict(list)
        for i, question in enumerate(self.questions):
            categories[question.category].append(i)
        return dict(categories)
    
    def _analyze_difficulties(self) -> Dict[str, List[int]]:
        """Analyze question distribution by difficulty"""
        difficulties = defaultdict(list)
        for i, question in enumerate(self.questions):
            difficulties[question.difficulty].append(i)
        return dict(difficulties)
    
    def _initialize_weights(self):
        """Initialize question weights based on rarity and balance"""
        total_questions = len(self.questions)
        
        if total_questions == 0:
            return
        
        for i, question in enumerate(self.questions):
            # Base weight
            weight = 1.0
            
            # Category balance weight (favor less common categories)
            category_size = len(self.category_distribution[question.category])
            if category_size > 0:
                category_weight = math.log(total_questions / category_size + 1)
            else:
                category_weight = 1.0
            
            # Difficulty balance weight
            difficulty_size = len(self.difficulty_distribution[question.difficulty])
            if difficulty_size > 0:
                difficulty_weight = math.log(total_questions / difficulty_size + 1)
            else:
                difficulty_weight = 1.0
            
            # Combine weights
            self.question_weights[i] = weight * category_weight * difficulty_weight
    
    def select_question_weighted_random(self, 
                                      used_questions: Set[int], 
                                      user_id: Optional[int] = None) -> Optional[QuizQuestion]:
        """Select question using weighted random selection"""
        available_indices = [i for i in range(len(self.questions)) if i not in used_questions]
        
        if not available_indices:
            logger.warning("No available questions for weighted random selection")
            return None
        
        # Filter out questions this user has seen recently (if user_id provided)
        if user_id and user_id in self.user_question_history:
            user_history = self.user_question_history[user_id]
            # Avoid questions seen in last 20 questions
            if len(user_history) > 20:
                recent_questions = set(list(user_history)[-20:])
                filtered_indices = [i for i in available_indices if i not in recent_questions]
                if filtered_indices:
                    available_indices = filtered_indices
        
        # Calculate weights for available questions
        weights = []
        for i in available_indices:
            base_weight = self.question_weights.get(i, 1.0)
            
            # Reduce weight for frequently used questions globally
            usage_penalty = 1.0 / (1.0 + self.global_question_usage[i] * 0.1)
            
            # Reduce weight for questions user has seen before
            user_penalty = 1.0
            if user_id and i in self.user_question_history.get(user_id, set()):
                user_penalty = 0.3  # Significantly reduce chance of repeat
            
            final_weight = base_weight * usage_penalty * user_penalty
            weights.append(max(final_weight, 0.01))  # Ensure minimum weight
        
        # Select using weighted random choice
        try:
            selected_index = random.choices(available_indices, weights=weights)[0]
        except (IndexError, ValueError) as e:
            logger.error(f"Error in weighted selection: {e}")
            selected_index = random.choice(available_indices)
        
        # Update tracking
        self.global_question_usage[selected_index] += 1
        if user_id:
            self.user_question_history[user_id].add(selected_index)
        
        logger.debug(f"Selected question {selected_index} using weighted random")
        return self.questions[selected_index]
    
    def select_question_balanced_categories(self, 
                                          used_questions: Set[int],
                                          target_category: Optional[str] = None) -> Optional[QuizQuestion]:
        """Select question ensuring category balance"""
        available_indices = [i for i in range(len(self.questions)) if i not in used_questions]
        
        if not available_indices:
            logger.warning("No available questions for balanced category selection")
            return None
        
        # Try to select from target category first
        if target_category and target_category in self.category_distribution:
            category_indices = [i for i in self.category_distribution[target_category] 
                              if i in available_indices]
            if category_indices:
                selected_index = random.choice(category_indices)
                self.global_question_usage[selected_index] += 1
                logger.debug(f"Selected question {selected_index} from target category {target_category}")
                return self.questions[selected_index]
        
        # Group available questions by category
        available_by_category = defaultdict(list)
        for i in available_indices:
            category = self.questions[i].category
            available_by_category[category].append(i)
        
        if not available_by_category:
            logger.warning("No questions available by category")
            return None
        
        # Select category with least usage in current session
        category_usage = defaultdict(int)
        for i in used_questions:
            if i < len(self.questions):
                category_usage[self.questions[i].category] += 1
        
        # Find category with minimum usage that has available questions
        available_categories = list(available_by_category.keys())
        min_usage = min(category_usage.get(cat, 0) for cat in available_categories)
        candidate_categories = [cat for cat in available_categories 
                              if category_usage.get(cat, 0) == min_usage]
        
        selected_category = random.choice(candidate_categories)
        selected_index = random.choice(available_by_category[selected_category])
        
        self.global_question_usage[selected_index] += 1
        logger.debug(f"Selected question {selected_index} from balanced category {selected_category}")
        return self.questions[selected_index]
    
    def select_question_difficulty_progression(self, 
                                             used_questions: Set[int],
                                             question_number: int,
                                             total_questions: int = 10) -> Optional[QuizQuestion]:
        """Select question with difficulty progression (easy -> medium -> hard)"""
        available_indices = [i for i in range(len(self.questions)) if i not in used_questions]
        
        if not available_indices:
            logger.warning("No available questions for difficulty progression")
            return None
        
        # Determine target difficulty based on question number
        progress = question_number / total_questions if total_questions > 0 else 0
        
        if progress <= 0.3:  # First 30% - easy questions
            target_difficulty = "easy"
        elif progress <= 0.7:  # Middle 40% - medium questions
            target_difficulty = "medium"
        else:  # Last 30% - hard questions
            target_difficulty = "hard"
        
        # Try to find questions of target difficulty
        target_indices = [i for i in available_indices 
                         if self.questions[i].difficulty == target_difficulty]
        
        if target_indices:
            selected_index = random.choice(target_indices)
            logger.debug(f"Selected question {selected_index} with target difficulty {target_difficulty}")
        else:
            # Fallback to any available question
            selected_index = random.choice(available_indices)
            actual_difficulty = self.questions[selected_index].difficulty
            logger.debug(f"Fallback: selected question {selected_index} with difficulty {actual_difficulty} (target was {target_difficulty})")
        
        self.global_question_usage[selected_index] += 1
        return self.questions[selected_index]
    
    def select_question_adaptive(self, 
                               used_questions: Set[int],
                               user_id: int,
                               user_performance: Dict[str, float]) -> Optional[QuizQuestion]:
        """Adaptive selection based on user performance"""
        available_indices = [i for i in range(len(self.questions)) if i not in used_questions]
        
        if not available_indices:
            logger.warning("No available questions for adaptive selection")
            return None
        
        # Get user's accuracy by difficulty
        easy_accuracy = user_performance.get('easy', 0.5)
        medium_accuracy = user_performance.get('medium', 0.5)
        hard_accuracy = user_performance.get('hard', 0.5)
        
        # Determine target difficulty based on performance
        if easy_accuracy < 0.6:
            target_difficulty = "easy"
            logger.debug(f"Adaptive: choosing easy (easy_acc={easy_accuracy:.2f})")
        elif medium_accuracy < 0.6:
            target_difficulty = "medium"
            logger.debug(f"Adaptive: choosing medium (medium_acc={medium_accuracy:.2f})")
        elif hard_accuracy < 0.8:
            target_difficulty = "hard"
            logger.debug(f"Adaptive: choosing hard (hard_acc={hard_accuracy:.2f})")
        else:
            # User is performing well, mix difficulties
            target_difficulty = random.choice(["medium", "hard"])
            logger.debug(f"Adaptive: user performing well, mixing with {target_difficulty}")
        
        # Filter by target difficulty
        target_indices = [i for i in available_indices 
                         if self.questions[i].difficulty == target_difficulty]
        
        if not target_indices:
            target_indices = available_indices
            logger.debug("Adaptive: no questions of target difficulty, using all available")
        
        # Apply user history filtering
        if user_id in self.user_question_history:
            user_history = self.user_question_history[user_id]
            if len(user_history) > 15:
                recent_questions = set(list(user_history)[-15:])
                filtered_indices = [i for i in target_indices if i not in recent_questions]
                if filtered_indices:
                    target_indices = filtered_indices
                    logger.debug(f"Adaptive: filtered out {len(recent_questions)} recent questions")
        
        selected_index = random.choice(target_indices)
        
        # Update tracking
        self.global_question_usage[selected_index] += 1
        if user_id:
            self.user_question_history[user_id].add(selected_index)
        
        actual_difficulty = self.questions[selected_index].difficulty
        logger.debug(f"Adaptive: selected question {selected_index} with difficulty {actual_difficulty}")
        return self.questions[selected_index]
    
    def select_question_simple_random(self, used_questions: Set[int], **kwargs) -> Optional[QuizQuestion]:
        """Simple random selection (fallback)"""
        available_indices = [i for i in range(len(self.questions)) if i not in used_questions]
        
        if not available_indices:
            logger.warning("No available questions for simple random selection")
            return None
        
        selected_index = random.choice(available_indices)
        self.global_question_usage[selected_index] += 1
        
        logger.debug(f"Selected question {selected_index} using simple random")
        return self.questions[selected_index]
    
    def get_selection_function(self, strategy: str):
        """Get selection function based on strategy name"""
        strategies = {
            "weighted_random": self.select_question_weighted_random,
            "balanced_categories": self.select_question_balanced_categories,
            "difficulty_progression": self.select_question_difficulty_progression,
            "adaptive": self.select_question_adaptive,
            "simple_random": self.select_question_simple_random
        }
        
        selected_func = strategies.get(strategy, self.select_question_weighted_random)
        logger.debug(f"Using selection strategy: {strategy}")
        return selected_func
    
    def get_statistics(self) -> Dict[str, any]:
        """Get selection statistics"""
        stats = {
            "total_questions": len(self.questions),
            "categories": len(self.category_distribution),
            "difficulties": len(self.difficulty_distribution),
            "global_usage": dict(self.global_question_usage),
            "user_histories": {uid: len(history) for uid, history in self.user_question_history.items()},
            "category_breakdown": {cat: len(indices) for cat, indices in self.category_distribution.items()},
            "difficulty_breakdown": {diff: len(indices) for diff, indices in self.difficulty_distribution.items()}
        }
        
        # Calculate usage statistics
        if self.global_question_usage:
            usage_values = list(self.global_question_usage.values())
            stats["usage_stats"] = {
                "min_usage": min(usage_values),
                "max_usage": max(usage_values),
                "avg_usage": sum(usage_values) / len(usage_values)
            }
        
        return stats
    
    def reset_user_history(self, user_id: int) -> bool:
        """Reset question history for a specific user"""
        if user_id in self.user_question_history:
            del self.user_question_history[user_id]
            logger.info(f"Reset question history for user {user_id}")
            return True
        return False
    
    def reset_global_usage(self) -> bool:
        """Reset global question usage statistics"""
        self.global_question_usage.clear()
        logger.info("Reset global question usage statistics")
        return True
    
    def add_questions(self, new_questions: List[QuizQuestion]) -> int:
        """Add new questions to the selector"""
        if not new_questions:
            return 0
        
        original_count = len(self.questions)
        self.questions.extend(new_questions)
        
        # Recalculate distributions and weights
        self.category_distribution = self._analyze_categories()
        self.difficulty_distribution = self._analyze_difficulties()
        self._initialize_weights()
        
        added_count = len(new_questions)
        logger.info(f"Added {added_count} questions to selector (total: {len(self.questions)})")
        return added_count
    
    def remove_question(self, question_index: int) -> bool:
        """Remove a question by index"""
        if 0 <= question_index < len(self.questions):
            removed_question = self.questions.pop(question_index)
            
            # Update all tracking data
            self._update_indices_after_removal(question_index)
            
            # Recalculate distributions and weights
            self.category_distribution = self._analyze_categories()
            self.difficulty_distribution = self._analyze_difficulties()
            self._initialize_weights()
            
            logger.info(f"Removed question {question_index}: {removed_question.question[:50]}...")
            return True
        
        logger.warning(f"Cannot remove question: index {question_index} out of range")
        return False
    
    def _update_indices_after_removal(self, removed_index: int):
        """Update all index-based tracking after question removal"""
        # Update global usage tracking
        new_global_usage = defaultdict(int)
        for idx, usage in self.global_question_usage.items():
            if idx < removed_index:
                new_global_usage[idx] = usage
            elif idx > removed_index:
                new_global_usage[idx - 1] = usage
            # Skip the removed index
        self.global_question_usage = new_global_usage
        
        # Update user question histories
        for user_id in self.user_question_history:
            old_history = self.user_question_history[user_id]
            new_history = set()
            for idx in old_history:
                if idx < removed_index:
                    new_history.add(idx)
                elif idx > removed_index:
                    new_history.add(idx - 1)
                # Skip the removed index
            self.user_question_history[user_id] = new_history
    
    def get_question_by_index(self, index: int) -> Optional[QuizQuestion]:
        """Get a question by its index"""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None
    
    def find_questions_by_category(self, category: str) -> List[int]:
        """Find all question indices for a given category"""
        return self.category_distribution.get(category, [])
    
    def find_questions_by_difficulty(self, difficulty: str) -> List[int]:
        """Find all question indices for a given difficulty"""
        return self.difficulty_distribution.get(difficulty, [])
    
    def get_least_used_questions(self, limit: int = 10) -> List[tuple]:
        """Get the least used questions with their usage counts"""
        if not self.global_question_usage:
            # If no usage data, return first questions
            return [(i, 0) for i in range(min(limit, len(self.questions)))]
        
        # Sort by usage count
        usage_items = list(self.global_question_usage.items())
        usage_items.sort(key=lambda x: x[1])
        
        return usage_items[:limit]
    
    def get_most_used_questions(self, limit: int = 10) -> List[tuple]:
        """Get the most used questions with their usage counts"""
        if not self.global_question_usage:
            return []
        
        # Sort by usage count (descending)
        usage_items = list(self.global_question_usage.items())
        usage_items.sort(key=lambda x: x[1], reverse=True)
        
        return usage_items[:limit]