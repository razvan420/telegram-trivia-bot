"""
Quiz service for managing quiz sessions and logic
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Set
from collections import defaultdict

from models.quiz_question import QuizQuestion
from services.question_selector import QuestionSelector
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)

class QuizService:
    """Service for managing quiz sessions and logic"""
    
    def __init__(self, question_selector: QuestionSelector, translation_service: TranslationService):
        self.question_selector = question_selector
        self.translation_service = translation_service
        self.active_quizzes: Dict[int, Dict[str, Any]] = {}  # chat_id -> quiz_data
        self.user_performance_tracking = defaultdict(lambda: defaultdict(list))
        self.selection_strategy = "weighted_random"
        
        logger.info("QuizService initialized")
    
    def start_quiz(self, chat_id: int, user_id: int, username: str, max_questions: int = 10) -> Optional[QuizQuestion]:
        """Start a new quiz session"""
        try:
            # Check if quiz is already running
            if chat_id in self.active_quizzes:
                logger.warning(f"Quiz already running in chat {chat_id}")
                return None
            
            # Select first question
            first_question = self._select_next_question(chat_id, user_id, is_first=True)
            if not first_question:
                logger.error(f"Could not select first question for chat {chat_id}")
                return None
            
            # Initialize quiz session
            self.active_quizzes[chat_id] = {
                'current_question': first_question,
                'question_count': 1,
                'max_questions': max_questions,
                'participants': {},
                'start_time': datetime.now(),
                'used_questions': {self._get_question_index(first_question)},
                'poll_id': None,
                'poll_message_id': None,
                'initiator_user_id': user_id,
                'language': 'ro'
            }
            
            logger.info(f"Started quiz in chat {chat_id} by user {user_id}")
            return first_question
            
        except Exception as e:
            logger.error(f"Error starting quiz in chat {chat_id}: {e}")
            return None
    
    def stop_quiz(self, chat_id: int) -> bool:
        """Stop an active quiz session"""
        try:
            if chat_id in self.active_quizzes:
                del self.active_quizzes[chat_id]
                logger.info(f"Stopped quiz in chat {chat_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping quiz in chat {chat_id}: {e}")
            return False
    
    def is_quiz_active(self, chat_id: int) -> bool:
        """Check if a quiz is active in the given chat"""
        return chat_id in self.active_quizzes
    
    def get_quiz_data(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get quiz data for a chat"""
        return self.active_quizzes.get(chat_id)
    
    def update_poll_info(self, chat_id: int, poll_id: str, message_id: int):
        """Update poll information for a quiz"""
        if chat_id in self.active_quizzes:
            self.active_quizzes[chat_id]['poll_id'] = poll_id
            self.active_quizzes[chat_id]['poll_message_id'] = message_id
            logger.debug(f"Updated poll info for chat {chat_id}: poll_id={poll_id}")
    
    def process_poll_answer(self, poll_id: str, user_id: int, username: str, 
                          selected_options: list) -> Optional[Dict[str, Any]]:
        """Process a poll answer and update scores"""
        try:
            # Find which chat this poll belongs to
            chat_id = None
            quiz_data = None
            
            for cid, data in self.active_quizzes.items():
                if data.get('poll_id') == poll_id:
                    chat_id = cid
                    quiz_data = data
                    break
            
            if not chat_id or not quiz_data:
                logger.warning(f"Could not find quiz for poll_id {poll_id}")
                return None
            
            current_question = quiz_data['current_question']
            
            # Check if answer is correct
            is_correct = (selected_options and 
                         len(selected_options) > 0 and
                         selected_options[0] == current_question.correct_answer)
            
            # Update quiz participants
            if user_id not in quiz_data['participants']:
                quiz_data['participants'][user_id] = {
                    'username': username,
                    'score': 0,
                    'answers': 0
                }
            
            participant = quiz_data['participants'][user_id]
            participant['answers'] += 1
            participant['username'] = username  # Update username
            
            if is_correct:
                participant['score'] += 1
            
            # Update performance tracking for enhanced selection
            self.update_user_performance(user_id, current_question, is_correct)
            
            logger.info(f"Processed answer from user {user_id} in chat {chat_id}: {'correct' if is_correct else 'incorrect'}")
            
            return {
                'chat_id': chat_id,
                'user_id': user_id,
                'is_correct': is_correct,
                'question': current_question,
                'participant_data': participant
            }
            
        except Exception as e:
            logger.error(f"Error processing poll answer: {e}")
            return None
    
    def get_next_question(self, chat_id: int) -> Optional[QuizQuestion]:
        """Get the next question for a quiz"""
        try:
            if chat_id not in self.active_quizzes:
                logger.warning(f"No active quiz in chat {chat_id}")
                return None
            
            quiz_data = self.active_quizzes[chat_id]
            quiz_data['question_count'] += 1
            
            # Check if quiz should end
            if quiz_data['question_count'] > quiz_data['max_questions']:
                logger.info(f"Quiz in chat {chat_id} reached max questions ({quiz_data['max_questions']})")
                return None
            
            # Select next question
            initiator_user_id = quiz_data.get('initiator_user_id', 0)
            next_question = self._select_next_question(chat_id, initiator_user_id)
            
            if next_question:
                quiz_data['current_question'] = next_question
                quiz_data['used_questions'].add(self._get_question_index(next_question))
                
                logger.info(f"Selected question {quiz_data['question_count']} for chat {chat_id}")
                return next_question
            
            logger.warning(f"Could not select next question for chat {chat_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting next question for chat {chat_id}: {e}")
            return None
    
    def get_quiz_results(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get quiz results"""
        try:
            if chat_id not in self.active_quizzes:
                logger.warning(f"No quiz data found for chat {chat_id}")
                return None
            
            quiz_data = self.active_quizzes[chat_id]
            participants = quiz_data['participants']
            
            if not participants:
                return {'participants': [], 'total_participants': 0}
            
            # Sort participants by score
            sorted_participants = sorted(
                participants.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            
            results = {
                'participants': sorted_participants,
                'total_participants': len(participants),
                'total_questions': quiz_data['question_count'] - 1,  # -1 because we increment before checking
                'start_time': quiz_data['start_time'],
                'duration': datetime.now() - quiz_data['start_time']
            }
            
            logger.info(f"Generated results for quiz in chat {chat_id}: {len(participants)} participants")
            return results
            
        except Exception as e:
            logger.error(f"Error getting quiz results for chat {chat_id}: {e}")
            return None
    
    def _select_next_question(self, chat_id: int, user_id: int, is_first: bool = False) -> Optional[QuizQuestion]:
        """Select the next question using the current strategy"""
        try:
            if chat_id not in self.active_quizzes and not is_first:
                return None
            
            # Get used questions
            if is_first:
                used_questions = set()
            else:
                quiz_data = self.active_quizzes[chat_id]
                used_questions = quiz_data.get('used_questions', set())
            
            # Get selection function
            selection_func = self.question_selector.get_selection_function(self.selection_strategy)
            
            # Select question based on strategy
            if self.selection_strategy == "adaptive":
                user_performance = self.calculate_user_performance(user_id)
                return selection_func(used_questions, user_id, user_performance)
            elif self.selection_strategy == "difficulty_progression" and not is_first:
                quiz_data = self.active_quizzes[chat_id]
                question_count = quiz_data.get('question_count', 1)
                max_questions = quiz_data.get('max_questions', 10)
                return selection_func(used_questions, question_count, max_questions)
            else:
                return selection_func(used_questions, user_id)
                
        except Exception as e:
            logger.error(f"Error in question selection for chat {chat_id}: {e}")
            return None
    
    def _get_question_index(self, question: QuizQuestion) -> int:
        """Get the index of a question in the questions list"""
        try:
            return self.question_selector.questions.index(question)
        except (ValueError, AttributeError):
            return -1
    
    def update_user_performance(self, user_id: int, question: QuizQuestion, is_correct: bool):
        """Update user performance tracking"""
        try:
            self.user_performance_tracking[user_id][question.difficulty].append(is_correct)
            
            # Keep only last 20 answers per difficulty
            for difficulty in self.user_performance_tracking[user_id]:
                if len(self.user_performance_tracking[user_id][difficulty]) > 20:
                    self.user_performance_tracking[user_id][difficulty] = \
                        self.user_performance_tracking[user_id][difficulty][-20:]
                        
        except Exception as e:
            logger.error(f"Error updating user performance: {e}")
    
    def calculate_user_performance(self, user_id: int) -> Dict[str, float]:
        """Calculate user performance by difficulty"""
        performance = {}
        user_data = self.user_performance_tracking[user_id]
        
        for difficulty in ["easy", "medium", "hard"]:
            if difficulty in user_data and user_data[difficulty]:
                correct_count = sum(user_data[difficulty])
                total_count = len(user_data[difficulty])
                performance[difficulty] = correct_count / total_count
            else:
                performance[difficulty] = 0.5  # Default neutral performance
        
        return performance
    
    def set_selection_strategy(self, strategy: str) -> bool:
        """Set the question selection strategy"""
        valid_strategies = ["weighted_random", "balanced_categories", "difficulty_progression", "adaptive", "simple_random"]
        if strategy in valid_strategies:
            self.selection_strategy = strategy
            logger.info(f"Changed selection strategy to: {strategy}")
            return True
        
        logger.warning(f"Invalid selection strategy: {strategy}")
        return False
    
    def get_selection_strategy(self) -> str:
        """Get the current selection strategy"""
        return self.selection_strategy
    
    def get_active_quizzes_count(self) -> int:
        """Get the number of active quizzes"""
        return len(self.active_quizzes)
    
    def get_active_quizzes(self) -> Dict[int, Dict[str, Any]]:
        """Get all active quizzes"""
        return self.active_quizzes.copy()
    
    def get_quiz_statistics(self) -> Dict[str, Any]:
        """Get overall quiz statistics"""
        total_participants = 0
        total_questions_asked = 0
        
        for quiz_data in self.active_quizzes.values():
            total_participants += len(quiz_data['participants'])
            total_questions_asked += quiz_data.get('question_count', 1) - 1
        
        return {
            'active_quizzes': len(self.active_quizzes),
            'total_participants': total_participants,
            'total_questions_asked': total_questions_asked,
            'current_strategy': self.selection_strategy,
            'performance_tracking_users': len(self.user_performance_tracking)
        }
    
    def cleanup_inactive_quizzes(self, max_age_hours: int = 24) -> int:
        """Clean up quizzes that have been inactive for too long"""
        try:
            current_time = datetime.now()
            inactive_chats = []
            
            for chat_id, quiz_data in self.active_quizzes.items():
                start_time = quiz_data.get('start_time', current_time)
                age = current_time - start_time
                
                if age.total_seconds() > (max_age_hours * 3600):
                    inactive_chats.append(chat_id)
            
            # Remove inactive quizzes
            for chat_id in inactive_chats:
                del self.active_quizzes[chat_id]
                logger.info(f"Cleaned up inactive quiz in chat {chat_id}")
            
            return len(inactive_chats)
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive quizzes: {e}")
            return 0
    
    def get_user_quiz_stats(self, user_id: int) -> Dict[str, Any]:
        """Get quiz statistics for a specific user"""
        stats = {
            'active_participations': 0,
            'performance_data': self.user_performance_tracking.get(user_id, {}),
            'current_performance': self.calculate_user_performance(user_id)
        }
        
        # Count active participations
        for quiz_data in self.active_quizzes.values():
            if user_id in quiz_data['participants']:
                stats['active_participations'] += 1
        
        return stats