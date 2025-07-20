import json
import time
import os
import requests
from datetime import datetime
from typing import List, Dict, Any
import urllib.parse

class RomanianTriviaTranslator:
    def __init__(self, service='libre'):
        """
        Initialize translator with different services:
        - 'libre': LibreTranslate (free, local or API)
        - 'mymemory': MyMemory API (free with limits)
        - 'manual': Manual translations with dictionary
        """
        self.service = service
        self.target_language = 'ro'
        self.source_language = 'en' 
        self.batch_size = 10
        self.delay_between_batches = 2
        self.backup_frequency = 50
        
        # Manual translation dictionary for common terms
        self.manual_translations = {
            # True/False
            "True": "Adevărat",
            "False": "Fals", 
            "true": "adevărat",
            "false": "fals",
            
            # Difficulties
            "easy": "ușor",
            "medium": "mediu",
            "hard": "greu",
            
            # Categories
            "General Knowledge": "Cultură Generală",
            "Entertainment: Books": "Divertisment: Cărți", 
            "Entertainment: Film": "Divertisment: Film",
            "Entertainment: Music": "Divertisment: Muzică",
            "Science & Nature": "Știință și Natură",
            "Sports": "Sport",
            "Geography": "Geografie",
            "History": "Istorie",
            "Politics": "Politică",
            "Art": "Artă",
            "Celebrities": "Celebrități",
            "Animals": "Animale",
            "Vehicles": "Vehicule",
            
            # Common words
            "What": "Ce",
            "Who": "Cine", 
            "Where": "Unde",
            "When": "Când",
            "Why": "De ce",
            "How": "Cum",
            "Which": "Care",
            "The": "",  # Romanian doesn't always need "the"
            "and": "și",
            "or": "sau",
            "but": "dar",
            "with": "cu",
            "from": "din",
            "to": "la",
            "in": "în",
            "on": "pe",
            "at": "la",
            "by": "de",
            "for": "pentru",
            "is": "este",
            "are": "sunt",
            "was": "a fost",
            "were": "au fost",
            "will": "va",
            "would": "ar",
            
            # Common answers
            "Yes": "Da",
            "No": "Nu",
            "All": "Toate",
            "None": "Niciunul",
            "Some": "Unele",
            "Many": "Multe",
            "Few": "Puține",
            "Most": "Majoritatea",
            "First": "Primul",
            "Last": "Ultimul",
            "Next": "Următorul",
            "Previous": "Precedentul",
            
            # Numbers as words
            "one": "unu",
            "two": "doi", 
            "three": "trei",
            "four": "patru",
            "five": "cinci",
            "six": "șase",
            "seven": "șapte",
            "eight": "opt",
            "nine": "nouă",
            "ten": "zece",
            
            # Common subjects
            "book": "carte",
            "movie": "film",
            "song": "cântec",
            "game": "joc",
            "country": "țară",
            "city": "oraș",
            "year": "an",
            "name": "nume",
            "color": "culoare",
            "number": "număr",
            "word": "cuvânt",
            "letter": "literă",
            "language": "limbă",
            "world": "lume",
            "people": "oameni",
            "person": "persoană",
            "man": "bărbat",
            "woman": "femeie",
            "child": "copil",
            "family": "familie",
            "friend": "prieten",
            "water": "apă",
            "food": "mâncare",
            "time": "timp",
            "day": "zi",
            "night": "noapte",
            "morning": "dimineață",
            "evening": "seară",
            "week": "săptămână",
            "month": "lună",
            "house": "casă",
            "car": "mașină",
            "money": "bani",
            "work": "muncă",
            "school": "școală",
            "university": "universitate",
            "music": "muzică",
            "art": "artă",
            "science": "știință",
            "history": "istorie",
            "politics": "politică",
            "sports": "sport",
            "health": "sănătate",
            "love": "dragoste",
            "life": "viață",
            "death": "moarte",
            "peace": "pace",
            "war": "război",
            "government": "guvern",
            "president": "președinte",
            "king": "rege",
            "queen": "regină",
            "capital": "capitală",
            "famous": "celebru",
            "important": "important",
            "beautiful": "frumos",
            "large": "mare",
            "small": "mic",
            "new": "nou",
            "old": "vechi",
            "good": "bun",
            "bad": "rău",
            "best": "cel mai bun",
            "worst": "cel mai rău",
            "first": "primul",
            "last": "ultimul",
            "next": "următorul",
            "big": "mare",
            "little": "mic",
            "long": "lung",
            "short": "scurt",
            "high": "înalt",
            "low": "jos",
            "right": "dreapta",
            "left": "stânga",
            "up": "sus",
            "down": "jos",
            "here": "aici",
            "there": "acolo",
            "now": "acum",
            "then": "atunci",
            "today": "astăzi",
            "tomorrow": "mâine",
            "yesterday": "ieri",
            "before": "înainte",
            "after": "după",
            "early": "devreme",
            "late": "târziu",
            "always": "întotdeauna",
            "never": "niciodată",
            "sometimes": "uneori",
            "usually": "de obicei",
            "often": "adesea",
            "again": "din nou",
            "once": "odată",
            "twice": "de două ori",
            "more": "mai mult",
            "less": "mai puțin",
            "most": "cel mai mult",
            "least": "cel mai puțin",
            "very": "foarte",
            "quite": "destul de",
            "too": "prea",
            "also": "de asemenea",
            "only": "doar",
            "just": "doar",
            "still": "încă",
            "already": "deja",
            "yet": "încă",
            "even": "chiar",
            "almost": "aproape",
            "enough": "destul",
            "together": "împreună",
            "alone": "singur",
            "each": "fiecare",
            "every": "fiecare",
            "all": "toate",
            "both": "ambele",
            "either": "oricare",
            "neither": "niciunul",
            "another": "altul",
            "other": "alt",
            "same": "același",
            "different": "diferit",
            "such": "astfel",
            "like": "ca",
            "than": "decât",
            "as": "ca",
            "so": "așa",
            "because": "pentru că",
            "if": "dacă",
            "when": "când",
            "where": "unde",
            "why": "de ce",
            "how": "cum",
            "what": "ce",
            "who": "cine",
            "which": "care",
            "whose": "al cui",
            "whom": "pe cine"
        }
        
        self.libre_url = "https://libretranslate.de/translate"  # Public LibreTranslate instance
        
    def translate_with_libre(self, text: str) -> str:
        """Translate using LibreTranslate API"""
        try:
            data = {
                'q': text,
                'source': self.source_language,
                'target': self.target_language,
                'format': 'text'
            }
            
            response = requests.post(self.libre_url, data=data)
            if response.status_code == 200:
                result = response.json()
                return result['translatedText']
            else:
                print(f"LibreTranslate error: {response.status_code}")
                return self.translate_manual(text)
        except Exception as e:
            print(f"LibreTranslate failed: {e}")
            return self.translate_manual(text)
    
    def translate_with_mymemory(self, text: str) -> str:
        """Translate using MyMemory API (free tier)"""
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': f'{self.source_language}|{self.target_language}'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result['responseStatus'] == 200:
                    return result['responseData']['translatedText']
            
            return self.translate_manual(text)
        except Exception as e:
            print(f"MyMemory failed: {e}")
            return self.translate_manual(text)
    
    def translate_manual(self, text: str) -> str:
        """Manual translation using dictionary + basic rules"""
        if not text:
            return text
            
        # Check if we have a direct translation
        if text in self.manual_translations:
            return self.manual_translations[text]
        
        # Split into words and translate word by word
        words = text.split()
        translated_words = []
        
        for word in words:
            # Remove punctuation for lookup
            clean_word = word.strip('.,!?;:"()[]{}').lower()
            
            # Check if we have translation
            if clean_word in self.manual_translations:
                # Preserve original capitalization
                translated = self.manual_translations[clean_word]
                if word[0].isupper() and translated:
                    translated = translated.capitalize()
                translated_words.append(translated)
            else:
                # Keep original word if no translation found
                translated_words.append(word)
        
        return ' '.join(filter(None, translated_words))
    
    def translate_text(self, text: str, max_retries: int = 3) -> str:
        """Translate text using selected service"""
        if not text or text.strip() == "":
            return text
        
        # Clean the text
        text = text.strip()
        
        for attempt in range(max_retries):
            try:
                if self.service == 'libre':
                    result = self.translate_with_libre(text)
                elif self.service == 'mymemory':
                    result = self.translate_with_mymemory(text)
                else:
                    result = self.translate_manual(text)
                
                if result and result != text:
                    return self.post_process_romanian(result)
                else:
                    # If translation failed, try manual as fallback
                    return self.translate_manual(text)
                    
            except Exception as e:
                print(f"⚠️ Translation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return self.translate_manual(text)
        
        return text
    
    def post_process_romanian(self, text: str) -> str:
        """Post-process Romanian text"""
        if not text:
            return text
            
        # Fix common issues
        text = text.replace(" de ", " din ").replace(" pentru ", " pentru ")
        
        # Ensure proper capitalization for True/False
        if text.lower() in ['adevărat', 'true']:
            return 'Adevărat'
        elif text.lower() in ['fals', 'false']:
            return 'Fals'
            
        return text
    
    def decode_category(self, category: str) -> str:
        """Decode URL-encoded category"""
        try:
            decoded = urllib.parse.unquote(category)
            if decoded in self.manual_translations:
                return self.manual_translations[decoded]
            return self.translate_text(decoded)
        except:
            return category
    
    def translate_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a single trivia question"""
        try:
            translated_question = question.copy()
            
            # Translate the main question
            original_q = question['question']
            print(f"🔄 Translating: {original_q[:60]}...")
            translated_question['question'] = self.translate_text(original_q)
            
            # Translate correct answer
            translated_question['correct_answer'] = self.translate_text(question['correct_answer'])
            
            # Translate incorrect answers
            translated_incorrect = []
            for incorrect in question['incorrect_answers']:
                translated_incorrect.append(self.translate_text(incorrect))
            translated_question['incorrect_answers'] = translated_incorrect
            
            # Translate category
            translated_question['category'] = self.decode_category(question['category'])
            
            # Translate difficulty
            difficulty = question['difficulty']
            if difficulty in self.manual_translations:
                translated_question['difficulty'] = self.manual_translations[difficulty]
            else:
                translated_question['difficulty'] = difficulty
            
            return translated_question
            
        except Exception as e:
            print(f"❌ Error translating question: {e}")
            return question
    
    def save_backup(self, translated_questions: List[Dict], progress: int):
        """Save backup of translated questions"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"romanian_backup_{progress}q_{timestamp}.json"
        backup_path = os.path.join("romanian_translations", backup_filename)
        
        os.makedirs("romanian_translations", exist_ok=True)
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(translated_questions, f, ensure_ascii=False, indent=2)
            print(f"💾 Backup saved: {backup_path}")
        except Exception as e:
            print(f"❌ Error saving backup: {e}")
    
    def translate_chunk_file(self, input_filename: str, output_filename: str = None):
        """Translate the chunk JSON file to Romanian"""
        if not output_filename:
            base_name = os.path.splitext(input_filename)[0]
            output_filename = f"{base_name}_romanian.json"
        
        print(f"🚀 Starting translation of {input_filename}")
        print(f"🎯 Target: Romanian (ro)")
        print(f"📁 Output: {output_filename}")
        print(f"🔧 Service: {self.service}")
        print("=" * 60)
        
        # Load the original JSON
        try:
            with open(input_filename, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            print(f"📊 Loaded {len(questions)} questions")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False
        
        if not isinstance(questions, list) or not questions:
            print("❌ Invalid JSON format. Expected a list of questions.")
            return False
        
        print(f"✅ JSON format validated")
        estimated_time_minutes = len(questions) * 2 / 60
        print(f"⏱️ Estimated time: {estimated_time_minutes:.1f} minutes")
        
        # Start translation
        translated_questions = []
        start_time = datetime.now()
        
        for i, question in enumerate(questions):
            try:
                translated_q = self.translate_question(question)
                translated_questions.append(translated_q)
                
                progress = i + 1
                percentage = (progress / len(questions)) * 100
                
                print(f"✅ {progress}/{len(questions)} ({percentage:.1f}%) - {translated_q['category']}")
                
                # Save backup periodically
                if progress % self.backup_frequency == 0:
                    self.save_backup(translated_questions, progress)
                
                # Rate limiting
                if progress % self.batch_size == 0 and self.service != 'manual':
                    print(f"⏳ Pausing {self.delay_between_batches}s...")
                    time.sleep(self.delay_between_batches)
                
            except KeyboardInterrupt:
                print(f"\n⏹️ Translation stopped by user at question {i + 1}")
                self.save_backup(translated_questions, len(translated_questions))
                return False
            except Exception as e:
                print(f"❌ Error with question {i + 1}: {e}")
                translated_questions.append(question)
                continue
        
        # Save final translated file
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(translated_questions, f, ensure_ascii=False, indent=2)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n🎉 TRANSLATION COMPLETE!")
            print(f"⏱️ Total time: {duration}")
            print(f"📊 Questions translated: {len(translated_questions)}")
            print(f"📁 Saved to: {output_filename}")
            
            # Show sample translated question
            if translated_questions:
                print(f"\n📄 Sample translated question:")
                sample = translated_questions[0]
                print(json.dumps(sample, indent=2, ensure_ascii=False))
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving final file: {e}")
            return False

def main():
    """Main function"""
    print("🇷🇴 ROMANIAN TRIVIA TRANSLATOR - Python 3.13 Compatible")
    print("=" * 60)
    print("📋 Translation services available:")
    print("   1. LibreTranslate (free online API)")
    print("   2. MyMemory (free API with limits)")
    print("   3. Manual dictionary (offline, basic)")
    
    # Choose service
    service_choice = input("\nChoose service (1/2/3) [default: 3]: ").strip()
    service_map = {'1': 'libre', '2': 'mymemory', '3': 'manual', '': 'manual'}
    service = service_map.get(service_choice, 'manual')
    
    translator = RomanianTriviaTranslator(service=service)
    
    # Check if chunk file exists
    chunk_file = "chunk_001_of_010.json"
    if os.path.exists(chunk_file):
        print(f"\n🎯 Found file: {chunk_file}")
        confirm = input("❓ Translate this file? (y/n): ")
        if confirm.lower() == 'y':
            success = translator.translate_chunk_file(chunk_file)
            if success:
                print(f"\n✅ Translation completed successfully!")
                return
    
    # Manual file input
    input_file = input("\n📁 Enter path to JSON file: ").strip()
    input_file = input_file.strip('"')
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    output_file = input("📁 Output filename (or Enter for auto): ").strip()
    if not output_file:
        output_file = None
    
    print(f"\n📋 Settings:")
    print(f"   📥 Input: {input_file}")
    print(f"   📤 Output: {output_file or 'Auto-generated'}")
    print(f"   🌍 Target language: Romanian")
    print(f"   🔧 Service: {service}")
    
    confirm = input("\n❓ Start translation? (y/n): ")
    if confirm.lower() != 'y':
        print("👋 Translation cancelled.")
        return
    
    success = translator.translate_chunk_file(input_file, output_file)
    
    if success:
        print(f"\n✅ Translation completed successfully!")
        print(f"🎯 Your Romanian trivia questions are ready!")
    else:
        print(f"\n❌ Translation was not completed.")
        print(f"💾 Check romanian_translations folder for partial progress.")

if __name__ == "__main__":
    main()