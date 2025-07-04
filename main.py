"""
Main entry point for the Telegram Quiz Bot
"""
import asyncio
import logging
import sys
from pathlib import Path

from telegram.ext import Application, CommandHandler, PollAnswerHandler, CallbackQueryHandler

# Import our modules
from config.settings import BOT_TOKEN, LOGGING_CONFIG, DATA_DIR
from models.quiz_question import QuizQuestion
from models.user_score import UserScore
from services.data_service import DataService
from services.question_selector import QuestionSelector
from services.quiz_service import QuizService
from services.translation_service import TranslationService
from handlers.command_handlers import CommandHandlers
from handlers.callback_handlers import CallbackHandlers
from utils.validators import validate_bot_token

# Configure logging
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class QuizBot:
    """Main Quiz Bot application class"""
    
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.application = None
        
        # Services
        self.data_service = DataService()
        self.translation_service = TranslationService()
        self.question_selector = None
        self.quiz_service = None
        
        # Handlers
        self.command_handlers = None
        self.callback_handlers = None
        
        # Initialize components
        self._validate_configuration()
        self._initialize_services()
        self._initialize_handlers()
    
    def _validate_configuration(self):
        """Validate bot configuration"""
        if not validate_bot_token(self.bot_token):
            logger.error("Invalid bot token! Please set TELEGRAM_BOT_TOKEN environment variable.")
            print("❌ Invalid bot token! Please set TELEGRAM_BOT_TOKEN environment variable.")
            print("💡 You can get a bot token from @BotFather on Telegram")
            sys.exit(1)
        
        # Ensure data directories exist
        DATA_DIR.mkdir(exist_ok=True)
        logger.info("Configuration validated successfully")
    
    def _initialize_services(self):
        """Initialize all services"""
        try:
            # Load questions
            questions = self.data_service.load_questions("ro")
            if not questions:
                logger.error("No questions loaded! Please ensure question files exist.")
                print("❌ No questions loaded! Please create question files in data/questions/")
                print("💡 Expected file: data/questions/ro-questions.json")
                print("\n💡 Each file should contain an array of questions in this format:")
                print('''
                [
                    {
                        "question": "Care este capitala României?",
                        "options": ["Sofia", "Budapesta", "București", "Belgrad"],
                        "correct_answer": 2,
                        "explanation": "București este capitala României.",
                        "difficulty": "easy",
                        "category": "geografie"
                    }
                ]
                ''')
                sys.exit(1)
            
            # Load user scores
            self.data_service.load_user_scores()
            
            # Initialize question selector
            self.question_selector = QuestionSelector(questions)
            
            # Initialize quiz service
            self.quiz_service = QuizService(self.question_selector, self.translation_service)
            
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            sys.exit(1)
    
    def _initialize_handlers(self):
        """Initialize command and callback handlers"""
        try:
            # Initialize Telegram application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Initialize handlers
            self.command_handlers = CommandHandlers(
                self.quiz_service,
                self.data_service,
                self.translation_service,
                self.application
            )
            
            self.callback_handlers = CallbackHandlers(
                self.quiz_service,
                self.data_service,
                self.translation_service
            )
            
            # Register handlers
            self._register_handlers()
            
            logger.info("Handlers initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing handlers: {e}")
            sys.exit(1)
    
    def _register_handlers(self):
        """Register all bot handlers"""
        try:
            # Command handlers
            self.application.add_handler(CommandHandler("start", self.command_handlers.start_command))
            self.application.add_handler(CommandHandler("goq", self.command_handlers.start_quiz_command))
            self.application.add_handler(CommandHandler("quiz_stop", self.command_handlers.stop_quiz_command))
            self.application.add_handler(CommandHandler("personal_score", self.command_handlers.show_scores_command))
            self.application.add_handler(CommandHandler("global_socre", self.command_handlers.leaderboard_command))
            self.application.add_handler(CommandHandler("quiz_help", self.command_handlers.help_command))
            self.application.add_handler(CommandHandler("quiz_strategy", self.command_handlers.strategy_command))
            
            # Poll answer handler
            self.application.add_handler(PollAnswerHandler(self.callback_handlers.handle_poll_answer))
            
            # Callback query handler (for inline keyboards if needed)
            self.application.add_handler(CallbackQueryHandler(self.callback_handlers.handle_callback_query))
            
            # Error handler
            self.application.add_error_handler(self.callback_handlers.handle_error)
            
            logger.info("All handlers registered successfully")
            
        except Exception as e:
            logger.error(f"Error registering handlers: {e}")
            raise
    
    async def _shutdown(self):
        """Proper cleanup on shutdown"""
        try:
            logger.info("Shutting down bot...")
            
            # Save any pending data
            if self.data_service:
                self.data_service.save_user_scores(self.data_service.user_scores)
                logger.info("Saved user scores")
            
            # Stop application
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Application stopped")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def print_startup_info(self):
        """Print bot startup information"""
        stats = self.data_service.get_question_statistics()
        quiz_stats = self.quiz_service.get_quiz_statistics()
        
        print("🚀 Enhanced Quiz Bot is running!")
        print(f"🧠 Question Selection Strategy: {self.quiz_service.get_selection_strategy()}")
        print(f"📚 Loaded Questions: {stats.get('total_questions', 0)} (Romanian)")
        print(f"👥 Registered Users: {len(self.data_service.user_scores)}")
        
        # Show category breakdown
        if 'by_category' in stats:
            print("📊 Categories:")
            for cat, count in stats['by_category'].items():
                print(f"   • {cat.replace('-', ' ').title()}: {count}")
        
        # Show difficulty breakdown  
        if 'by_difficulty' in stats:
            print("🎯 Difficulties:")
            for diff, count in stats['by_difficulty'].items():
                print(f"   • {diff.title()}: {count}")
        
        print("🔄 Available Commands:")
        print("   • /start - Welcome message")
        print("   • /goq - Start new quiz")
        print("   • /quiz_stop - Stop current quiz (admins only)")
        print("   • /personal_score - View personal statistics")
        print("   • /global_socre - View leaderboard")
        print("   • /quiz_help - Show help information")
        print("   • /quiz_strategy - Change selection strategy (admins only)")
        print("\nPress Ctrl+C to stop the bot")
    
    async def run(self):
        """Run the bot"""
        try:
            logger.info("Starting Enhanced Quiz Bot...")
            
            # Initialize and start application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling
            await self.application.updater.start_polling(
                allowed_updates=['message', 'poll_answer', 'callback_query'],
                drop_pending_updates=True,
                timeout=10
            )
            
            # Print startup information
            self.print_startup_info()
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Bot shutdown requested by user")
            print("\n👋 Bot stopped by user")
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            print(f"❌ Fatal error: {e}")
        finally:
            await self._shutdown()

async def main():
    """Main function"""
    try:
        # Create and run bot
        bot = QuizBot()
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())