"""
Translation service for multilingual support
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for handling translations and text management"""
    
    def __init__(self):
        self.translations = {
            "ro": {
                "welcome": "🎯 **Bun venit la Quiz Bot!** 🎯\n\nApasă /goq pentru a începe un quiz!",
                "goqed": "🎯 Quiz început! Răspunde la întrebări pe măsură ce apar.",
                "quiz_stopped": "⏹️ Quiz oprit!",
                "quiz_ended": "🏁 Quiz terminat!",
                "no_questions": "❌ Nu sunt întrebări disponibile!",
                "quiz_running": "⚠️ Un quiz este deja pornit! Folosește /quiz_stop pentru a-l opri.",
                "admin_only": "❌ Doar adminii pot opri quiz-ul!",
                "no_active_quiz": "❌ Nu există quiz activ de oprit!",
                "no_participation": "📊 Nu ai participat la niciun quiz încă!",
                "no_scores": "📊 Nu sunt scoruri înregistrate încă!",
                "question_number": "🎯 **Întrebarea #{0}/{1}**",
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
                "help_scoring": "**🏆 Sistem de Punctaj:**",
                "categories_loaded": "📚 **Categorii încărcate:**",
                "strategy_changed": "✅ Strategia quiz-ului schimbată la: **{0}**",
                "invalid_strategy": "❌ Strategie invalidă. Opțiuni valide: {0}",
                "current_strategy": "🎯 **Strategia Curentă:** {0}",
                "available_strategies": "**Strategii Disponibile:**",
                "strategy_usage": "**Utilizare:** `/quiz_strategy [nume_strategie]`",
                "error_permissions": "Eroare la verificarea permisiunilor",
                "performance_by_difficulty": "**📈 Performanță pe Dificultate:**",
                "no_data_yet": "Nu există date încă",
                "strategies": {
                    "weighted_random": "Selecție inteligentă cu istoricul utilizatorului",
                    "balanced_categories": "Distribuție echilibrată a categoriilor", 
                    "difficulty_progression": "Ușor → Mediu → Greu",
                    "adaptive": "Se adaptează la performanța utilizatorului",
                    "simple_random": "Selecție aleatoare de bază"
                },
                "commands": {
                    "start": "Mesaj de bun venit",
                    "goq": "Începe un nou quiz", 
                    "quiz_stop": "Oprește quiz-ul curent (doar pentru admini)",
                    "personal_score": "Vezi statisticile tale personale",
                    "global_score": "Vezi clasamentul jucătorilor",
                    "quiz_help": "Afișează acest mesaj de ajutor",
                    "quiz_strategy": "Schimbă strategia de selecție (admini)"
                },
                "features": [
                    "🎮 Quiz-uri interactive cu întrebări cu alegere multiplă",
                    "🏆 Sistem de punctaj și clasament", 
                    "📊 Statistici personale detaliate",
                    "⏱️ Întrebări cu timp limitat (15 secunde)",
                    "🎯 10 întrebări per sesiune de quiz",
                    "🧠 Selecție inteligentă de întrebări",
                    "🎲 Multiple strategii de selecție"
                ],
                "how_to_play": [
                    "1. Folosește `/goq` pentru a începe un quiz",
                    "2. Răspunde la întrebări făcând clic pe opțiunea corectă", 
                    "3. Ai 15 secunde pentru fiecare întrebare",
                    "4. Quiz-ul se termină după 10 întrebări",
                    "5. Vezi rezultatele și clasamentul la final"
                ],
                "scoring_rules": [
                    "• +1 punct pentru fiecare răspuns correct",
                    "• Statistici detaliate includ acuratețea și activitatea",
                    "• Clasamentul se bazează pe scorul total", 
                    "• Progresul se salvează automat",
                    "• Selecția inteligentă se adaptează la performanța ta"
                ]
            }
        }
    
    def get_text(self, key: str, language: str = "ro", **kwargs) -> str:
        """Get translated text for a given key"""
        if language not in self.translations:
            language = "ro"  # Fallback to Romanian
        
        text = self.translations[language].get(key, key)
        
        # Handle formatting if kwargs provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError, IndexError) as e:
                # Log the error and return unformatted text
                logger.warning(f"Text formatting error for key '{key}': {e}")
                pass  # Return unformatted text if formatting fails
        
        return text
    
    def get_question_number_text(self, current: int, total: int, language: str = "ro") -> str:
        """Get formatted question number text"""
        try:
            template = self.translations[language].get("question_number", "🎯 **Întrebarea #{0}/{1}**")
            return template.format(current, total)
        except (KeyError, ValueError, IndexError):
            # Fallback formatting
            return f"🎯 **Întrebarea #{current}/{total}**"
    
    def get_commands_text(self, language: str = "ro") -> str:
        """Get formatted commands help text"""
        commands = self.translations[language]["commands"]
        commands_text = ""
        
        for command, description in commands.items():
            commands_text += f"• `/{command}` - {description}\n"
        
        return commands_text.strip()
    
    def get_features_text(self, language: str = "ro") -> str:
        """Get formatted features text"""
        features = self.translations[language]["features"]
        return "\n".join(features)
    
    def get_how_to_play_text(self, language: str = "ro") -> str:
        """Get formatted how to play text"""
        steps = self.translations[language]["how_to_play"]
        return "\n".join(steps)
    
    def get_scoring_text(self, language: str = "ro") -> str:
        """Get formatted scoring rules text"""
        rules = self.translations[language]["scoring_rules"]
        return "\n".join(rules)
    
    def get_strategies_text(self, language: str = "ro") -> str:
        """Get formatted strategies text"""
        strategies = self.translations[language]["strategies"]
        strategies_text = ""
        
        for strategy, description in strategies.items():
            strategies_text += f"• `{strategy}` - {description}\n"
        
        return strategies_text.strip()
    
    def format_user_stats(self, user_score, performance: dict, language: str = "ro") -> str:
        """Format user statistics text"""
        accuracy = user_score.accuracy
        
        performance_text = ""
        if any(perf > 0 for perf in performance.values()):
            performance_lines = []
            for difficulty, perf in performance.items():
                if perf > 0:
                    performance_lines.append(f"  • {difficulty.title()}: {perf*100:.1f}%")
            performance_text = "\n".join(performance_lines)
        else:
            performance_text = f"  {self.get_text('no_data_yet', language)}"
        
        # Use safe string formatting
        stats_text = f"""
{self.get_text('your_stats', language)}

{self.get_text('player', language)} {user_score.username}
{self.get_text('total_score', language)} {user_score.total_score}
{self.get_text('questions_answered', language)} {user_score.questions_answered}
{self.get_text('correct_answers', language)} {user_score.correct_answers}
{self.get_text('accuracy', language)} {accuracy:.1f}%
{self.get_text('last_activity', language)} {user_score.get_last_activity_date()}

{self.get_text('performance_by_difficulty', language)}
{performance_text}
        """
        
        return stats_text.strip()
    
    def format_strategy_changed_text(self, strategy: str, language: str = "ro") -> str:
        """Format strategy changed text safely"""
        try:
            template = self.translations[language].get("strategy_changed", "✅ Strategia quiz-ului schimbată la: **{0}**")
            return template.format(strategy)
        except (KeyError, ValueError, IndexError):
            return f"✅ Strategia quiz-ului schimbată la: **{strategy}**"
    
    def format_current_strategy_text(self, strategy: str, language: str = "ro") -> str:
        """Format current strategy text safely"""
        try:
            template = self.translations[language].get("current_strategy", "🎯 **Strategia Curentă:** {0}")
            return template.format(strategy)
        except (KeyError, ValueError, IndexError):
            return f"🎯 **Strategia Curentă:** {strategy}"
    
    def format_leaderboard(self, sorted_users, language: str = "ro") -> str:
        """Format leaderboard text"""
        if not sorted_users:
            return self.get_text('no_scores', language)
        
        leaderboard_text = f"{self.get_text('leaderboard', language)}\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_score in enumerate(sorted_users[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            accuracy = user_score.accuracy
            leaderboard_text += f"{medal} **{user_score.username}** - {user_score.total_score} pct ({accuracy:.1f}%)\n"
        
        return leaderboard_text.strip()