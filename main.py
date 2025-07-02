import asyncio
import logging
import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    Poll,
    ChatMemberOwner,
    ChatMemberAdministrator
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class QuizQuestion:
    """Data class for quiz questions"""
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    difficulty: str = "medium"
    category: str = "general"

@dataclass
class UserScore:
    """Data class for user scores"""
    user_id: int
    username: str
    total_score: int = 0
    questions_answered: int = 0
    correct_answers: int = 0
    last_activity: str = ""
    preferred_language: str = "en"

class QuizBot:
    """Main Telegram Quiz Bot class"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.questions_en: List[QuizQuestion] = []
        self.questions_ro: List[QuizQuestion] = []
        self.user_scores: Dict[int, UserScore] = {}
        self.active_quizzes: Dict[int, Dict] = {}  # chat_id -> quiz_data
        self.scores_file = Path("user_scores.json")
        
        # Language files
        self.en_questions_file = Path("en-questions.json")
        self.ro_questions_file = Path("ro-questions.json")
        
        # Translations
        self.translations = {
            "en": {
                "welcome": "🎯 **Welcome to Quiz Bot!** 🎯\n\nSelect your preferred language and start playing!",
                "language_selected": "✅ Language set to English!",
                "quiz_started": "🎯 Quiz started! Answer the questions as they appear.",
                "quiz_stopped": "⏹️ Quiz stopped!",
                "quiz_ended": "🏁 Quiz ended!",
                "no_questions": "❌ No questions available!",
                "quiz_running": "⚠️ A quiz is already running! Use /quiz-stop to end it first.",
                "admin_only": "❌ Only admins can stop the quiz!",
                "no_active_quiz": "❌ No active quiz to stop!",
                "no_participation": "📊 You haven't participated in any quizzes yet!",
                "no_scores": "📊 No scores recorded yet!",
                "question_number": "🎯 **Question #{}/10**",
                "quiz_results": "🏆 **Quiz Results** 🏆",
                "no_participants": "🏁 Quiz ended! No one participated. 😢",
                "your_stats": "📊 **Your Quiz Statistics**",
                "leaderboard": "🏆 **Quiz Leaderboard - Top 10** 🏆",
                "player": "👤 **Player:**",
                "total_score": "🎯 **Total Score:**",
                "questions_answered": "❓ **Questions Answered:**",
                "correct_answers": "✅ **Correct Answers:**",
                "accuracy": "📈 **Accuracy:**",
                "last_activity": "🕐 **Last Activity:**",
                "help_title": "🤖 **Quiz Bot Help** 🤖",
                "help_description": "Welcome to Quiz Bot! This bot allows you to play interactive quiz games in your Telegram chat.",
                "help_features": "**🎯 Features:**",
                "help_commands": "**📋 Available Commands:**",
                "help_how_to_play": "**🎮 How to Play:**",
                "help_languages": "**🌍 Supported Languages:**",
                "help_scoring": "**🏆 Scoring System:**"
            },
            "ro": {
                "welcome": "🎯 **Bun venit la Quiz Bot!** 🎯\n\nSelectează limba preferată și începe să joci!",
                "language_selected": "✅ Limba setată la Română!",
                "quiz_started": "🎯 Quiz început! Răspunde la întrebări pe măsură ce apar.",
                "quiz_stopped": "⏹️ Quiz oprit!",
                "quiz_ended": "🏁 Quiz terminat!",
                "no_questions": "❌ Nu sunt întrebări disponibile!",
                "quiz_running": "⚠️ Un quiz este deja pornit! Folosește /quiz-stop pentru a-l opri.",
                "admin_only": "❌ Doar adminii pot opri quiz-ul!",
                "no_active_quiz": "❌ Nu există quiz activ de oprit!",
                "no_participation": "📊 Nu ai participat la niciun quiz încă!",
                "no_scores": "📊 Nu sunt scoruri înregistrate încă!",
                "question_number": "🎯 **Întrebarea #{}/10**",
                "quiz_results": "🏆 **Rezultatele Quiz-ului** 🏆",
                "no_participants": "🏁 Quiz terminat! Nimeni nu a participat. 😢",
                "your_stats": "📊 **Statisticile Tale**",
                "leaderboard": "🏆 **Clasamentul Quiz-ului - Top 10** 🏆",
                "player": "👤 **Jucător:**",
                "total_score": "🎯 **Scor Total:**",
                "questions_answered": "❓ **Întrebări Răspunse:**",
                "correct_answers": "✅ **Răspunsuri Corecte:**",
                "accuracy": "📈 **Acuratețe:**",
                "last_activity": "🕐 **Ultima Activitate:**",
                "help_title": "🤖 **Ajutor Quiz Bot** 🤖",
                "help_description": "Bun venit la Quiz Bot! Acest bot îți permite să joci jocuri interactive de quiz în chat-ul tău Telegram.",
                "help_features": "**🎯 Funcționalități:**",
                "help_commands": "**📋 Comenzi Disponibile:**",
                "help_how_to_play": "**🎮 Cum să Joci:**",
                "help_languages": "**🌍 Limbi Suportate:**",
                "help_scoring": "**🏆 Sistem de Punctaj:**"
            }
        }
        
        # Load existing data
        self.load_data()
        
        # Initialize application
        self.init_application()
        
        # Register handlers
        self.register_handlers()
    
    def init_application(self):
        """Initialize the Telegram application"""
        self.application = Application.builder().token(self.token).build()
    
    def validate_question(self, q_data: dict) -> Optional[QuizQuestion]:
        """Validate question structure"""
        required_fields = ['question', 'options', 'correct_answer']
        if not all(field in q_data for field in required_fields):
            return None
            
        if not isinstance(q_data['options'], list) or len(q_data['options']) < 2:
            return None
            
        try:
            correct_idx = int(q_data['correct_answer'])
            if not 0 <= correct_idx < len(q_data['options']):
                return None
        except (ValueError, TypeError):
            return None
            
        return QuizQuestion(
            question=q_data['question'],
            options=q_data['options'],
            correct_answer=correct_idx,
            explanation=q_data.get('explanation', ''),
            difficulty=q_data.get('difficulty', 'medium'),
            category=q_data.get('category', 'general')
        )
    
    def load_questions_from_file(self, file_path: Path) -> List[QuizQuestion]:
        """Load questions from a specific JSON file with validation"""
        questions = []
        try:
            if not file_path.exists():
                logger.warning(f"Question file not found: {file_path}")
                return questions
                
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    questions_data = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in file: {file_path}")
                    return questions
                    
                questions_list = []
                if isinstance(questions_data, list):
                    questions_list = questions_data
                elif isinstance(questions_data, dict) and 'questions' in questions_data:
                    questions_list = questions_data['questions']
                
                for i, q_data in enumerate(questions_list):
                    try:
                        question = self.validate_question(q_data)
                        if question:
                            questions.append(question)
                    except Exception as e:
                        logger.error(f"Error parsing question {i+1}: {e}")
                        continue
                
                logger.info(f"Loaded {len(questions)} questions from {file_path}")
        except Exception as e:
            logger.error(f"Error loading questions from {file_path}: {e}")
        
        return questions
    
    def load_data(self):
        """Load questions and scores from files"""
        # Load English questions
        self.questions_en = self.load_questions_from_file(self.en_questions_file)
        
        # Load Romanian questions
        self.questions_ro = self.load_questions_from_file(self.ro_questions_file)
        
        # Load user scores
        try:
            if self.scores_file.exists():
                with open(self.scores_file, 'r', encoding='utf-8') as f:
                    scores_data = json.load(f)
                    self.user_scores = {
                        int(uid): UserScore(**data) 
                        for uid, data in scores_data.items()
                    }
                    logger.info(f"Loaded scores for {len(self.user_scores)} users")
        except Exception as e:
            logger.error(f"Error loading scores: {e}")
    
    def save_data(self):
        """Atomic save with backup"""
        try:
            scores_data = {str(uid): asdict(score) for uid, score in self.user_scores.items()}
            
            # Write to temp file first
            temp_path = self.scores_file.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(scores_data, f, indent=2, ensure_ascii=False)
                
            # Create backup
            if self.scores_file.exists():
                backup_path = self.scores_file.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.unlink()
                self.scores_file.rename(backup_path)
                
            # Move temp to main
            temp_path.rename(self.scores_file)
            
        except Exception as e:
            logger.error(f"Critical save error: {e}")
            # Attempt to restore from backup if available
            if 'backup_path' in locals() and backup_path.exists():
                try:
                    backup_path.rename(self.scores_file)
                except Exception as restore_error:
                    logger.critical(f"Failed to restore backup: {restore_error}")
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        if user_id in self.user_scores:
            return self.user_scores[user_id].preferred_language
        return "en"
    
    def get_text(self, user_id: int, key: str) -> str:
        """Get translated text for user"""
        language = self.get_user_language(user_id)
        return self.translations[language].get(key, self.translations["en"].get(key, key))
    
    def get_questions_for_language(self, language: str) -> List[QuizQuestion]:
        """Get questions for specific language"""
        if language == "ro":
            return self.questions_ro
        return self.questions_en
    
    def register_handlers(self):
        """Register all command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("quiz_start", self.start_quiz_command))
        self.application.add_handler(CommandHandler("quiz_stop", self.stop_quiz_command))
        self.application.add_handler(CommandHandler("quiz_score", self.show_scores_command))
        self.application.add_handler(CommandHandler("quiz_leaderboard", self.leaderboard_command))
        self.application.add_handler(CommandHandler("quiz_help", self.help_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Poll answer handler
        self.application.add_handler(PollAnswerHandler(self.handle_poll_answer))
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_help command"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == "ro":
            help_text = f"""
{self.get_text(user_id, 'help_title')}

{self.get_text(user_id, 'help_description')}

{self.get_text(user_id, 'help_features')}
• 🎮 Quiz-uri interactive cu întrebări cu alegere multiplă
• 🌍 Suport pentru limbile română și engleză
• 🏆 Sistem de punctaj și clasament
• 📊 Statistici personale detaliate
• ⏱️ Întrebări cu timp limitat (15 secunde)
• 🎯 10 întrebări per sesiune de quiz

{self.get_text(user_id, 'help_commands')}
• `/quiz_start` - Începe un nou quiz
• `/quiz_stop` - Oprește quiz-ul curent (doar pentru admini)
• `/quiz_score` - Vezi statisticile tale personale
• `/quiz_leaderboard` - Vezi clasamentul jucătorilor
• `/quiz_help` - Afișează acest mesaj de ajutor

{self.get_text(user_id, 'help_how_to_play')}
1. Folosește `/quiz_start` pentru a începe un quiz
2. Selectează limba preferată la prima utilizare
3. Răspunde la întrebări făcând clic pe opțiunea corectă
4. Ai 15 secunde pentru fiecare întrebare
5. Quiz-ul se termină după 10 întrebări
6. Vezi rezultatele și clasamentul la final

{self.get_text(user_id, 'help_languages')}
• 🇺🇸 English
• 🇷🇴 Română

{self.get_text(user_id, 'help_scoring')}
• +1 punct pentru fiecare răspuns correct
• Statistici detaliate includ acuratețea și activitatea
• Clasamentul se bazează pe scorul total
• Progresul se salvează automat
            """
        else:
            help_text = f"""
{self.get_text(user_id, 'help_title')}

{self.get_text(user_id, 'help_description')}

{self.get_text(user_id, 'help_features')}
• 🎮 Interactive quizzes with multiple-choice questions
• 🌍 Support for English and Romanian languages
• 🏆 Scoring system and leaderboards
• 📊 Detailed personal statistics
• ⏱️ Timed questions (15 seconds each)
• 🎯 10 questions per quiz session

{self.get_text(user_id, 'help_commands')}
• `/quiz_start` - Start a new quiz
• `/quiz_stop` - Stop current quiz (admins only)
• `/quiz_score` - View your personal statistics
• `/quiz_leaderboard` - View player leaderboard
• `/quiz_help` - Show this help message

{self.get_text(user_id, 'help_how_to_play')}
1. Use `/quiz_start` to begin a quiz
2. Select your preferred language on first use
3. Answer questions by clicking the correct option
4. You have 15 seconds for each question
5. Quiz ends after 10 questions
6. View results and leaderboard at the end

{self.get_text(user_id, 'help_languages')}
• 🇺🇸 English
• 🇷🇴 Română

{self.get_text(user_id, 'help_scoring')}
• +1 point for each correct answer
• Detailed stats include accuracy and activity
• Leaderboard based on total score
• Progress is automatically saved
            """
        
        await update.message.reply_text(help_text.strip(), parse_mode=ParseMode.MARKDOWN)
    
    async def start_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_start command"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Check if user exists in scores, if not create with language selection
        if user_id not in self.user_scores:
            keyboard = [
                [
                    InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
                    InlineKeyboardButton("🇷🇴 Română", callback_data="lang_ro")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🌍 **Select your language / Selectează limba:**",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        user_language = self.get_user_language(user_id)
        questions = self.get_questions_for_language(user_language)
        
        if not questions:
            await update.message.reply_text(self.get_text(user_id, "no_questions"))
            return
        
        # Check if quiz is already running
        if chat_id in self.active_quizzes:
            await update.message.reply_text(self.get_text(user_id, "quiz_running"))
            return
        
        # Ensure clean state - remove any leftover quiz data
        if chat_id in self.active_quizzes:
            del self.active_quizzes[chat_id]
        
        # Start quiz with fresh state
        quiz_question = random.choice(questions)
        self.active_quizzes[chat_id] = {
            'current_question': quiz_question,
            'question_count': 1,
            'max_questions': 10,
            'participants': {},
            'start_time': datetime.now(),
            'available_questions': questions.copy(),  # Make a copy to avoid reference issues
            'used_questions': [quiz_question],
            'language': user_language,
            'poll_id': None,
            'poll_message_id': None
        }
        
        await update.message.reply_text(self.get_text(user_id, "quiz_started"))
        
        # Add a small delay to ensure message is sent before poll
        await asyncio.sleep(0.5)
        await self.send_quiz_question(chat_id, quiz_question, user_language)
    
    async def send_quiz_question(self, chat_id: int, question: QuizQuestion, language: str):
        """Send a quiz question as a poll"""
        try:
            if chat_id not in self.active_quizzes:
                logger.warning(f"Attempted to send question to inactive quiz in chat {chat_id}")
                return
                
            quiz_data = self.active_quizzes[chat_id]
            
            question_text = f"{self.translations[language]['question_number'].format(quiz_data['question_count'])}\n\n{question.question}"
            
            # Send poll
            poll_message = await self.application.bot.send_poll(
                chat_id=chat_id,
                question=question_text,
                options=question.options,
                type=Poll.QUIZ,
                correct_option_id=question.correct_answer,
                explanation=question.explanation or f"The correct answer is: {question.options[question.correct_answer]}",
                is_anonymous=False,
                open_period=15  # 15 seconds to answer
            )
            
            # Update quiz data with poll info
            quiz_data['poll_id'] = poll_message.poll.id
            quiz_data['poll_message_id'] = poll_message.message_id
            
            logger.info(f"Sent question {quiz_data['question_count']} to chat {chat_id}")
            
            # Schedule next question
            asyncio.create_task(self.schedule_next_question(chat_id, 20))
            
        except Exception as e:
            logger.error(f"Error sending quiz question to chat {chat_id}: {e}")
            await self.end_quiz(chat_id)
    
    async def schedule_next_question(self, chat_id: int, delay: int):
        """Schedule the next question after a delay"""
        try:
            await asyncio.sleep(delay)
            
            # Check if quiz is still active
            if chat_id not in self.active_quizzes:
                logger.info(f"Quiz in chat {chat_id} was stopped, cancelling next question")
                return
                
            quiz_data = self.active_quizzes[chat_id]
            quiz_data['question_count'] += 1
            
            if quiz_data['question_count'] > quiz_data['max_questions']:
                logger.info(f"Quiz in chat {chat_id} reached max questions, ending")
                await self.end_quiz(chat_id)
                return
                
            available_questions = quiz_data.get('available_questions', [])
            used_questions = quiz_data.get('used_questions', [])
            language = quiz_data.get('language', 'en')
            
            # Find remaining questions
            remaining_questions = [q for q in available_questions if q not in used_questions]
            
            # If no remaining questions, reset used questions
            if not remaining_questions:
                remaining_questions = available_questions
                quiz_data['used_questions'] = []
                logger.info(f"Reset used questions for chat {chat_id}")
            
            # Select random question
            next_question = random.choice(remaining_questions)
            quiz_data['current_question'] = next_question
            quiz_data['used_questions'].append(next_question)
            
            logger.info(f"Scheduling question {quiz_data['question_count']} for chat {chat_id}")
            await self.send_quiz_question(chat_id, next_question, language)
            
        except Exception as e:
            logger.error(f"Error in question scheduling for chat {chat_id}: {e}")
            if chat_id in self.active_quizzes:
                await self.end_quiz(chat_id)
    
    async def handle_poll_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle poll answers with robust scoring"""
        try:
            poll_answer = update.poll_answer
            user = poll_answer.user
            chat_id = None
            
            # Find which chat this poll belongs to
            for cid, quiz_data in self.active_quizzes.items():
                if quiz_data.get('poll_id') == poll_answer.poll_id:
                    chat_id = cid
                    break
            
            if not chat_id:
                return
                
            quiz_data = self.active_quizzes[chat_id]
            current_question = quiz_data['current_question']
            
            # Initialize user if not exists
            if user.id not in self.user_scores:
                self.user_scores[user.id] = UserScore(
                    user_id=user.id,
                    username=user.username or user.first_name or f"User_{user.id}",
                    preferred_language=quiz_data.get('language', 'en'),
                    last_activity=datetime.now().isoformat()
                )
            
            user_score = self.user_scores[user.id]
            user_score.questions_answered += 1
            user_score.last_activity = datetime.now().isoformat()
            
            # Check if answer is correct
            selected_options = poll_answer.option_ids
            if selected_options and selected_options[0] == current_question.correct_answer:
                user_score.correct_answers += 1
                user_score.total_score += 1
                quiz_data['participants'][user.id] = quiz_data['participants'].get(user.id, 0) + 1
            else:
                if user.id not in quiz_data['participants']:
                    quiz_data['participants'][user.id] = 0
            
            self.save_data()
        except Exception as e:
            logger.error(f"Error handling poll answer: {e}")
    
    async def end_quiz(self, chat_id: int):
        """End the quiz and show results with error handling"""
        try:
            if chat_id not in self.active_quizzes:
                return
                
            quiz_data = self.active_quizzes[chat_id]
            participants = quiz_data['participants']
            language = quiz_data.get('language', 'en')
            
            # Clear the current poll if it exists
            if 'poll_message_id' in quiz_data and quiz_data['poll_message_id']:
                try:
                    await self.application.bot.stop_poll(
                        chat_id=chat_id,
                        message_id=quiz_data['poll_message_id']
                    )
                except Exception as e:
                    logger.error(f"Error stopping poll: {e}")
            
            # Clean up quiz data immediately
            del self.active_quizzes[chat_id]
            
            if not participants:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=self.translations[language]["no_participants"]
                )
            else:
                sorted_participants = sorted(
                    participants.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                results_text = f"{self.translations[language]['quiz_results']}\n\n"
                medals = ["🥇", "🥈", "🥉"]
                
                for i, (user_id, score) in enumerate(sorted_participants[:5]):
                    user_data = self.user_scores.get(user_id)
                    username = user_data.username if user_data else "Unknown"
                    medal = medals[i] if i < 3 else f"{i+1}."
                    results_text += f"{medal} {username}: {score} points\n"
                
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=results_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            
        except Exception as e:
            logger.error(f"Error ending quiz: {e}")
            # Ensure cleanup even if there's an error
            if chat_id in self.active_quizzes:
                del self.active_quizzes[chat_id]
    
    async def stop_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_stop command with proper admin validation"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if not (isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)) or member.status != 'administrator'):
                await update.message.reply_text(self.get_text(user_id, "admin_only"))
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            await update.message.reply_text("Error verifying permissions")
            return
            
        if chat_id not in self.active_quizzes:
            await update.message.reply_text(self.get_text(user_id, "no_active_quiz"))
            return
        
        await self.end_quiz(chat_id)
        await update.message.reply_text(self.get_text(user_id, "quiz_stopped"))
    
    async def show_scores_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_score command with proper formatting"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_scores:
            await update.message.reply_text(self.get_text(user_id, "no_participation"))
            return
        
        user_score = self.user_scores[user_id]
        accuracy = (user_score.correct_answers / user_score.questions_answered * 100) if user_score.questions_answered > 0 else 0
        
        stats_text = f"""
        {self.get_text(user_id, 'your_stats')}

        {self.get_text(user_id, 'player')} {user_score.username}
        {self.get_text(user_id, 'total_score')} {user_score.total_score}
        {self.get_text(user_id, 'questions_answered')} {user_score.questions_answered}
        {self.get_text(user_id, 'correct_answers')} {user_score.correct_answers}
        {self.get_text(user_id, 'accuracy')} {accuracy:.1f}%
        {self.get_text(user_id, 'last_activity')} {user_score.last_activity.split('T')[0] if user_score.last_activity else 'Never'}
        """
        
        await update.message.reply_text(stats_text.strip(), parse_mode=ParseMode.MARKDOWN)
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_leaderboard command with proper formatting"""
        user_id = update.effective_user.id
        
        if not self.user_scores:
            await update.message.reply_text(self.get_text(user_id, "no_scores"))
            return
        
        sorted_users = sorted(
            self.user_scores.values(),
            key=lambda x: x.total_score,
            reverse=True
        )
        
        leaderboard_text = f"{self.get_text(user_id, 'leaderboard')}\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_score in enumerate(sorted_users[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            accuracy = (user_score.correct_answers / user_score.questions_answered * 100) if user_score.questions_answered > 0 else 0
            leaderboard_text += f"{medal} **{user_score.username}** - {user_score.total_score} pts ({accuracy:.1f}%)\n"
        
        await update.message.reply_text(leaderboard_text.strip(), parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries with error handling"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            
            if query.data.startswith("lang_"):
                language = query.data.split("_")[1]
                
                # Create or update user score with language preference
                if user_id not in self.user_scores:
                    self.user_scores[user_id] = UserScore(
                        user_id=user_id,
                        username=query.from_user.username or query.from_user.first_name or "Unknown",
                        preferred_language=language
                    )
                else:
                    self.user_scores[user_id].preferred_language = language
                
                self.save_data()
                
                await query.edit_message_text(
                    self.get_text(user_id, "language_selected"),
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Show welcome message
                await query.message.reply_text(
                    self.get_text(user_id, "welcome"),
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
    
    async def _shutdown(self):
        """Proper cleanup on shutdown"""
        try:
            if hasattr(self, 'application'):
                if hasattr(self.application, 'updater'):
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            self.save_data()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run(self):
        """Main bot run loop with proper error handling"""
        logger.info("Starting Quiz Bot with enhanced error handling...")
        
        try:
            await self.application.initialize()
            await self.application.start()
            
            if not hasattr(self.application, 'updater'):
                raise RuntimeError("Application updater not initialized")
                
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                timeout=10
            )
            
            logger.info("Bot is running!")
            print("🚀 Quiz Bot is running!")
            print("🔄 Commands: /quiz_start, /quiz_stop, /quiz_score, /quiz_leaderboard, /quiz_help")
            print("Press Ctrl+C to stop the bot")
            
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Bot shutdown requested")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
        finally:
            await self._shutdown()

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

async def main():
    """Main function to run the bot with proper initialization"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please replace BOT_TOKEN with your actual Telegram bot token!")
        return
    
    try:
        bot = QuizBot(BOT_TOKEN)
        
        if not bot.questions_en and not bot.questions_ro:
            print("❌ No questions loaded! Please create en-questions.json and ro-questions.json files.")
            return
        
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())