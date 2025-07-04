"""
Callback handlers for the Telegram Quiz Bot
"""
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from services.quiz_service import QuizService
from services.data_service import DataService
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)

class CallbackHandlers:
    """Handles callback queries and poll answers"""
    
    def __init__(self, quiz_service: QuizService, data_service: DataService, 
                 translation_service: TranslationService):
        self.quiz_service = quiz_service
        self.data_service = data_service
        self.translation_service = translation_service
    
    async def handle_poll_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle poll answers with robust scoring and performance tracking"""
        try:
            poll_answer = update.poll_answer
            user = poll_answer.user
            
            # Process the poll answer
            answer_result = self.quiz_service.process_poll_answer(
                poll_answer.poll_id,
                user.id,
                user.username or user.first_name or f"User_{user.id}",
                poll_answer.option_ids
            )
            
            if not answer_result:
                logger.warning(f"Could not process poll answer from user {user.id}")
                return
            
            # Update user score in data service
            user_score = self.data_service.get_user_score(
                answer_result['user_id'],
                answer_result['participant_data']['username']
            )
            
            # Add the answer to user's statistics
            user_score.add_answer(answer_result['is_correct'], points=1)
            
            # Save updated scores
            success = self.data_service.save_user_scores(self.data_service.user_scores)
            if not success:
                logger.error("Failed to save user scores after poll answer")
            
            logger.info(f"Updated score for user {user.id}: {user_score.total_score} total points")
            
        except Exception as e:
            logger.error(f"Error handling poll answer: {e}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Parse callback data
            callback_data = query.data
            
            if callback_data.startswith("quiz_"):
                await self._handle_quiz_callback(query, callback_data)
            elif callback_data.startswith("help_"):
                await self._handle_help_callback(query, callback_data)
            else:
                logger.warning(f"Unknown callback data: {callback_data}")
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
    
    async def _handle_quiz_callback(self, query, callback_data: str):
        """Handle quiz-related callbacks"""
        try:
            action = callback_data.replace("quiz_", "")
            
            if action == "start":
                # Start quiz callback
                chat_id = query.message.chat_id
                user_id = query.from_user.id
                username = query.from_user.username or query.from_user.first_name or f"User_{user_id}"
                
                if self.quiz_service.is_quiz_active(chat_id):
                    await query.edit_message_text("⚠️ Un quiz este deja activ!")
                    return
                
                # Start quiz logic would go here
                await query.edit_message_text("🎯 Quiz pornit! Răspunde la întrebări.")
                
            elif action == "stop":
                # Stop quiz callback
                chat_id = query.message.chat_id
                
                if not self.quiz_service.is_quiz_active(chat_id):
                    await query.edit_message_text("❌ Nu există quiz activ!")
                    return
                
                # Stop quiz logic would go here
                await query.edit_message_text("⏹️ Quiz oprit!")
                
            elif action == "stats":
                # Show stats callback
                user_id = query.from_user.id
                
                if user_id not in self.data_service.user_scores:
                    await query.edit_message_text("📊 Nu ai participat la niciun quiz încă!")
                    return
                
                user_score = self.data_service.user_scores[user_id]
                performance = self.quiz_service.calculate_user_performance(user_id)
                stats_text = self.translation_service.format_user_stats(user_score, performance)
                
                await query.edit_message_text(stats_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error handling quiz callback: {e}")
            await query.edit_message_text("❌ Eroare la procesarea comenzii!")
    
    async def _handle_help_callback(self, query, callback_data: str):
        """Handle help-related callbacks"""
        try:
            help_section = callback_data.replace("help_", "")
            
            if help_section == "commands":
                commands_text = self.translation_service.get_commands_text()
                help_text = f"**📋 Comenzi Disponibile:**\n\n{commands_text}"
                
            elif help_section == "features":
                features_text = self.translation_service.get_features_text()
                help_text = f"**🎯 Funcționalități:**\n\n{features_text}"
                
            elif help_section == "how_to_play":
                play_text = self.translation_service.get_how_to_play_text()
                help_text = f"**🎮 Cum să Joci:**\n\n{play_text}"
                
            elif help_section == "scoring":
                scoring_text = self.translation_service.get_scoring_text()
                help_text = f"**🏆 Sistem de Punctaj:**\n\n{scoring_text}"
                
            else:
                help_text = "❌ Secțiune de ajutor necunoscută!"
            
            await query.edit_message_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error handling help callback: {e}")
            await query.edit_message_text("❌ Eroare la afișarea ajutorului!")
    
    async def handle_inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline queries (if needed for future features)"""
        try:
            inline_query = update.inline_query
            query_text = inline_query.query
            
            # For now, just log the inline query
            logger.info(f"Received inline query: {query_text}")
            
            # You can implement inline query responses here in the future
            # For example, allowing users to share quiz questions or results
            
        except Exception as e:
            logger.error(f"Error handling inline query: {e}")
    
    async def handle_chosen_inline_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle chosen inline results (if needed for future features)"""
        try:
            chosen_result = update.chosen_inline_result
            result_id = chosen_result.result_id
            
            logger.info(f"User chose inline result: {result_id}")
            
            # You can implement tracking of chosen inline results here
            
        except Exception as e:
            logger.error(f"Error handling chosen inline result: {e}")
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pre-checkout queries (for future payment features)"""
        try:
            pre_checkout_query = update.pre_checkout_query
            
            # For now, just approve all payments (if implemented)
            await pre_checkout_query.answer(ok=True)
            
            logger.info(f"Pre-checkout query from user {pre_checkout_query.from_user.id}")
            
        except Exception as e:
            logger.error(f"Error handling pre-checkout query: {e}")
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle successful payments (for future premium features)"""
        try:
            payment = update.message.successful_payment
            user_id = update.effective_user.id
            
            logger.info(f"Successful payment from user {user_id}: {payment.total_amount}")
            
            # You can implement premium feature unlocking here
            
        except Exception as e:
            logger.error(f"Error handling successful payment: {e}")
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        try:
            logger.error(f"Update {update} caused error {context.error}")
            
            # You can implement error reporting or recovery logic here
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    def get_quiz_statistics(self) -> dict:
        """Get statistics for monitoring purposes"""
        try:
            return {
                'active_quizzes': self.quiz_service.get_active_quizzes_count(),
                'total_users': len(self.data_service.user_scores),
                'total_questions': len(self.data_service.questions),
                'selection_strategy': self.quiz_service.get_selection_strategy(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}