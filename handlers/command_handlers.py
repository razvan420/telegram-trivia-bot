"""
Command handlers for the Telegram Quiz Bot
"""
import asyncio
import logging
from datetime import datetime
from collections import defaultdict

from telegram import Update, ChatMemberOwner, ChatMemberAdministrator
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.quiz_service import QuizService
from services.data_service import DataService
from services.translation_service import TranslationService
from config.settings import SELECTION_STRATEGIES

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Handles all command-based interactions"""
    
    def __init__(self, quiz_service: QuizService, data_service: DataService, 
                 translation_service: TranslationService, bot_application):
        self.quiz_service = quiz_service
        self.data_service = data_service
        self.translation_service = translation_service
        self.bot_application = bot_application
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            welcome_text = self.translation_service.get_text("welcome")
            await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
    
    async def start_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /goq command"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            username = update.effective_user.username or update.effective_user.first_name or f"User_{user_id}"
            
            # Initialize user if not exists
            user_score = self.data_service.get_user_score(user_id, username)
            
            # Check if questions are available
            if not self.data_service.questions:
                no_questions_text = self.translation_service.get_text("no_questions")
                await update.message.reply_text(no_questions_text)
                return
            
            # Check if quiz is already running
            if self.quiz_service.is_quiz_active(chat_id):
                quiz_running_text = self.translation_service.get_text("quiz_running")
                await update.message.reply_text(quiz_running_text)
                return
            
            # Start quiz
            first_question = self.quiz_service.start_quiz(chat_id, user_id, username)
            if not first_question:
                no_questions_text = self.translation_service.get_text("no_questions")
                await update.message.reply_text(no_questions_text)
                return
            
            # Send confirmation
            goqed_text = self.translation_service.get_text("goqed")
            await update.message.reply_text(goqed_text)
            
            # Add a small delay to ensure message is sent before poll
            await asyncio.sleep(0.5)
            await self._send_quiz_question(chat_id, first_question)
            
        except Exception as e:
            logger.error(f"Error in start_quiz_command: {e}")
            await update.message.reply_text("❌ Eroare la începerea quiz-ului!")
    
    async def stop_quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_stop command"""
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            # Check admin permissions
            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                if not isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
                    admin_only_text = self.translation_service.get_text("admin_only")
                    await update.message.reply_text(admin_only_text)
                    return
            except Exception as e:
                error_text = self.translation_service.get_text("error_permissions")
                await update.message.reply_text(error_text)
                return
            
            # Check if quiz is active
            if not self.quiz_service.is_quiz_active(chat_id):
                no_active_text = self.translation_service.get_text("no_active_quiz")
                await update.message.reply_text(no_active_text)
                return
            
            # Stop quiz and show results
            await self._end_quiz(chat_id)
            
            quiz_stopped_text = self.translation_service.get_text("quiz_stopped")
            await update.message.reply_text(quiz_stopped_text)
            
        except Exception as e:
            logger.error(f"Error in stop_quiz_command: {e}")
    
    async def show_scores_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /personal_score command"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username or update.effective_user.first_name or f"User_{user_id}"
            
            # Get user score
            if user_id not in self.data_service.user_scores:
                no_participation_text = self.translation_service.get_text("no_participation")
                await update.message.reply_text(no_participation_text)
                return
            
            user_score = self.data_service.user_scores[user_id]
            
            # Get performance by difficulty
            performance = self.quiz_service.calculate_user_performance(user_id)
            
            # Format statistics
            stats_text = self.translation_service.format_user_stats(user_score, performance)
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error in show_scores_command: {e}")
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /global_socre command"""
        try:
            if not self.data_service.user_scores:
                no_scores_text = self.translation_service.get_text("no_scores")
                await update.message.reply_text(no_scores_text)
                return
            
            sorted_users = sorted(
                self.data_service.user_scores.values(),
                key=lambda x: x.total_score,
                reverse=True
            )
            
            leaderboard_text = self.translation_service.format_leaderboard(sorted_users)
            await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error in leaderboard_command: {e}")
    
    async def strategy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_strategy command"""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            # Check if user is admin
            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                if not isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
                    admin_only_text = self.translation_service.get_text("admin_only")
                    await update.message.reply_text(admin_only_text)
                    return
            except:
                pass
            
            if context.args:
                strategy = context.args[0].lower()
                
                if strategy in SELECTION_STRATEGIES:
                    self.quiz_service.set_selection_strategy(strategy)
                    strategy_changed_text = self.translation_service.format_strategy_changed_text(strategy)
                    await update.message.reply_text(strategy_changed_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    invalid_strategy_text = f"❌ Strategie invalidă. Opțiuni valide: {', '.join(SELECTION_STRATEGIES)}"
                    await update.message.reply_text(invalid_strategy_text)
            else:
                current_strategy = self.quiz_service.get_selection_strategy()
                strategies_text = self.translation_service.get_strategies_text()
                current_strategy_text = self.translation_service.format_current_strategy_text(current_strategy)
                
                response_text = f"""
{current_strategy_text}

{self.translation_service.get_text("available_strategies")}
{strategies_text}

{self.translation_service.get_text("strategy_usage")}
                """.strip()
                
                await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
                
        except Exception as e:
            logger.error(f"Error in strategy_command: {e}")
            await update.message.reply_text("❌ Eroare la procesarea comenzii!")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz_help command"""
        try:
            # Get question statistics
            stats = self.data_service.get_question_statistics()
            
            categories_text = ""
            if 'by_category' in stats:
                categories_lines = []
                for cat, count in stats['by_category'].items():
                    category_name = cat.replace('-', ' ').title()
                    categories_lines.append(f"• {category_name}: {count} întrebări")
                categories_text = "\n".join(categories_lines)
            
            difficulty_text = ""
            if 'by_difficulty' in stats:
                difficulty_lines = []
                for diff, count in stats['by_difficulty'].items():
                    difficulty_lines.append(f"• {diff.title()}: {count} întrebări")
                difficulty_text = "\n".join(difficulty_lines)
            
            total_questions = stats.get('total_questions', 0)
            
            help_text = f"""
{self.translation_service.get_text('help_title')}

{self.translation_service.get_text('help_description')}

{self.translation_service.get_text('help_features')}
{self.translation_service.get_features_text()}

{self.translation_service.get_text('help_commands')}
{self.translation_service.get_commands_text()}

{self.translation_service.get_text('help_how_to_play')}
{self.translation_service.get_how_to_play_text()}

{self.translation_service.get_text('categories_loaded')}
{categories_text}

**📊 Distribuția pe Dificultate:**
{difficulty_text}

{self.translation_service.get_text('help_scoring')}
{self.translation_service.get_scoring_text()}

**📈 Total Întrebări:** {total_questions}
            """.strip()
            
            await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
    
    async def _send_quiz_question(self, chat_id: int, question):
        """Send a quiz question as a poll"""
        try:
            quiz_data = self.quiz_service.get_quiz_data(chat_id)
            if not quiz_data:
                logger.warning(f"Attempted to send question to inactive quiz in chat {chat_id}")
                return
            
            # Format question text safely (no markdown)
            question_count = quiz_data['question_count']
            max_questions = quiz_data['max_questions']
            
            # Simple text formatting without markdown
            question_text = f"🎯 Întrebarea #{question_count}/{max_questions}\n\n{question.question}"
            
            # Send poll
            poll_message = await self.bot_application.bot.send_poll(
                chat_id=chat_id,
                question=question_text,
                options=question.options,
                type='quiz',
                correct_option_id=question.correct_answer,
                explanation=question.explanation or f"Răspunsul corect este: {question.options[question.correct_answer]}",
                is_anonymous=False,
                open_period=15  # 15 seconds to answer
            )
            
            # Update quiz data with poll info
            self.quiz_service.update_poll_info(chat_id, poll_message.poll.id, poll_message.message_id)
            
            logger.info(f"Sent question {quiz_data['question_count']} to chat {chat_id}")
            
            # Schedule next question
            asyncio.create_task(self._schedule_next_question(chat_id, 20))
            
        except Exception as e:
            logger.error(f"Error sending quiz question to chat {chat_id}: {e}")
            await self._end_quiz(chat_id)
    
    async def _schedule_next_question(self, chat_id: int, delay: int):
        """Schedule the next question after a delay"""
        try:
            await asyncio.sleep(delay)
            
            # Check if quiz is still active
            if not self.quiz_service.is_quiz_active(chat_id):
                logger.info(f"Quiz in chat {chat_id} was stopped, cancelling next question")
                return
            
            # Get next question
            next_question = self.quiz_service.get_next_question(chat_id)
            
            if next_question:
                logger.info(f"Scheduling next question for chat {chat_id}")
                await self._send_quiz_question(chat_id, next_question)
            else:
                # Quiz ended
                logger.info(f"Quiz in chat {chat_id} reached max questions, ending")
                await self._end_quiz(chat_id)
                
        except Exception as e:
            logger.error(f"Error in question scheduling for chat {chat_id}: {e}")
            if self.quiz_service.is_quiz_active(chat_id):
                await self._end_quiz(chat_id)
    
    async def _end_quiz(self, chat_id: int):
        """End the quiz and show results"""
        try:
            # Get results before ending quiz
            results = self.quiz_service.get_quiz_results(chat_id)
            
            # Clear the current poll if it exists
            quiz_data = self.quiz_service.get_quiz_data(chat_id)
            if quiz_data and 'poll_message_id' in quiz_data and quiz_data['poll_message_id']:
                try:
                    await self.bot_application.bot.stop_poll(
                        chat_id=chat_id,
                        message_id=quiz_data['poll_message_id']
                    )
                except Exception as e:
                    # This is expected if the poll already closed naturally
                    logger.debug(f"Could not stop poll (likely already closed): {e}")
            
            # Stop the quiz
            self.quiz_service.stop_quiz(chat_id)
            
            # Show results
            if not results or results['total_participants'] == 0:
                await self.bot_application.bot.send_message(
                    chat_id=chat_id, 
                    text="🏁 Quiz terminat! Nimeni nu a participat. 😢"
                )
            else:
                # Log results for debugging
                logger.info(f"Quiz results for chat {chat_id}: {results['total_participants']} participants")
                
                # Format results safely with plain text only
                results_text = "🏆 Rezultatele Quiz-ului 🏆\n\n"
                medals = ["🥇", "🥈", "🥉"]
                
                for i, (user_id, participant_data) in enumerate(results['participants'][:5]):
                    username = participant_data.get('username', f'User_{user_id}')
                    score = participant_data.get('score', 0)
                    medal = medals[i] if i < 3 else f"{i+1}."
                    
                    logger.info(f"Participant {i+1}: {username} with {score} points")
                    
                    # Clean username - remove any special characters that might cause issues
                    clean_username = ''.join(c for c in username if c.isalnum() or c in ' _-.')
                    if not clean_username:
                        clean_username = f'User_{user_id}'
                    
                    results_text += f"{medal} {clean_username}: {score} puncte\n"
                
                logger.info(f"Sending results message: {results_text}")
                
                # Send with plain text only
                await self.bot_application.bot.send_message(
                    chat_id=chat_id,
                    text=results_text
                )
            
        except Exception as e:
            logger.error(f"Error ending quiz: {e}")
            # Send a simple fallback message
            try:
                await self.bot_application.bot.send_message(
                    chat_id=chat_id,
                    text="🏁 Quiz terminat!"
                )
            except Exception as e2:
                logger.error(f"Error sending fallback message: {e2}")
            
            # Ensure cleanup even if there's an error
            self.quiz_service.stop_quiz(chat_id)