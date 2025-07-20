import requests
import json
import time
import html
import os
from datetime import datetime
from urllib.parse import unquote

class FastTriviaDBScraper:
    def __init__(self):
        self.base_url = "https://opentdb.com/api.php"
        self.category_url = "https://opentdb.com/api_category.php"
        self.count_url = "https://opentdb.com/api_count.php"
        self.global_count_url = "https://opentdb.com/api_count_global.php"
        self.token_url = "https://opentdb.com/api_token.php"
        self.session_token = None
        self.rate_limit_delay = 5.2  # 5.2 seconds between requests
        
    def get_session_token(self):
        """Get a fresh session token"""
        try:
            response = requests.get(f"{self.token_url}?command=request")
            if response.status_code == 200:
                data = response.json()
                if data['response_code'] == 0:
                    self.session_token = data['token']
                    print(f"✅ Session token obtained: {self.session_token}")
                    return True
            print("❌ Could not get session token")
            return False
        except Exception as e:
            print(f"❌ Error getting token: {e}")
            return False
    
    def reset_session_token(self):
        """Reset the session token when exhausted"""
        if self.session_token:
            try:
                reset_url = f"{self.token_url}?command=reset&token={self.session_token}"
                response = requests.get(reset_url)
                if response.status_code == 200:
                    data = response.json()
                    if data['response_code'] == 0:
                        print("🔄 Session token reset successfully")
                        return True
                print("⚠️ Could not reset token")
            except Exception as e:
                print(f"❌ Error resetting token: {e}")
        
        return self.get_session_token()
    
    def get_global_question_count(self):
        """Get total number of questions in the database"""
        try:
            response = requests.get(self.global_count_url)
            if response.status_code == 200:
                data = response.json()
                total_verified = data['overall']['total_num_of_verified_questions']
                print(f"📊 Total verified questions in DB: {total_verified}")
                return data
            return None
        except Exception as e:
            print(f"❌ Error getting global count: {e}")
            return None
    
    def get_category_counts(self):
        """Get question count for each category"""
        try:
            response = requests.get(self.category_url)
            if response.status_code == 200:
                categories = response.json()['trivia_categories']
                
                category_counts = []
                for category in categories:
                    time.sleep(self.rate_limit_delay)
                    
                    count_response = requests.get(f"{self.count_url}?category={category['id']}")
                    if count_response.status_code == 200:
                        count_data = count_response.json()
                        total_questions = count_data['category_question_count']['total_question_count']
                        
                        category_info = {
                            'id': category['id'],
                            'name': category['name'],
                            'total_questions': total_questions,
                            'easy': count_data['category_question_count']['total_easy_question_count'],
                            'medium': count_data['category_question_count']['total_medium_question_count'],
                            'hard': count_data['category_question_count']['total_hard_question_count']
                        }
                        category_counts.append(category_info)
                        print(f"📈 {category['name']}: {total_questions} questions")
                
                return category_counts
            return []
        except Exception as e:
            print(f"❌ Error getting categories: {e}")
            return []
    
    def fetch_questions_batch(self, amount=50, category=None, difficulty=None, question_type=None):
        """Fetch a batch of questions with proper encoding"""
        params = {
            'amount': min(amount, 50),
            'encode': 'url3986'  # Use URL encoding to handle special characters
        }
        
        if self.session_token:
            params['token'] = self.session_token
        
        if category:
            params['category'] = category
        
        if difficulty:
            params['difficulty'] = difficulty
        
        if question_type:
            params['type'] = question_type
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Fetch error: {e}")
            return None
    
    def decode_text(self, text):
        """Properly decode URL-encoded and HTML-encoded text"""
        if not text:
            return ""
        
        try:
            # First decode URL encoding (for url3986 encoding)
            decoded = unquote(text, encoding='utf-8')
            # Then decode HTML entities
            decoded = html.unescape(decoded)
            return decoded
        except Exception as e:
            print(f"⚠️ Decoding error for text '{text}': {e}")
            # Fallback: just decode HTML entities
            return html.unescape(text)
    
    def process_questions(self, questions_data):
        """Process questions into the exact desired format with proper encoding"""
        if not questions_data or 'results' not in questions_data:
            return []
        
        processed_questions = []
        
        for question in questions_data['results']:
            try:
                # Properly decode all text fields
                question_text = self.decode_text(question['question'])
                correct_answer = self.decode_text(question['correct_answer'])
                
                incorrect_answers = []
                for ans in question['incorrect_answers']:
                    incorrect_answers.append(self.decode_text(ans))
                
                # Create the exact format you specified
                formatted_question = {
                    "question": question_text,
                    "correct_answer": correct_answer,
                    "incorrect_answers": incorrect_answers,
                    "category": question['category'],
                    "difficulty": question['difficulty']
                }
                
                processed_questions.append(formatted_question)
                
            except Exception as e:
                print(f"⚠️ Error processing question: {e}")
                continue
        
        return processed_questions
    
    def download_all_questions_from_category(self, category_info):
        """Download ALL questions from a category"""
        category_id = category_info['id']
        category_name = category_info['name']
        total_questions = category_info['total_questions']
        
        if total_questions == 0:
            print(f"⏭️ Category '{category_name}' has no questions")
            return []
        
        print(f"\n🎯 Downloading category: {category_name}")
        print(f"📊 Total questions to download: {total_questions}")
        
        all_category_questions = []
        downloaded = 0
        
        while downloaded < total_questions:
            remaining = total_questions - downloaded
            batch_size = min(50, remaining)
            
            print(f"📥 Downloading batch: {downloaded + 1}-{downloaded + batch_size} of {total_questions}")
            
            time.sleep(self.rate_limit_delay)
            
            questions_data = self.fetch_questions_batch(
                amount=batch_size,
                category=category_id
            )
            
            if not questions_data:
                print(f"❌ Error downloading batch")
                break
            
            if questions_data['response_code'] == 0:
                batch_questions = self.process_questions(questions_data)
                all_category_questions.extend(batch_questions)
                downloaded += len(questions_data['results'])
                print(f"✅ Downloaded: {len(batch_questions)} questions (Total: {downloaded}/{total_questions})")
                
            elif questions_data['response_code'] == 1:
                print(f"ℹ️ No more questions available in this category")
                break
                
            elif questions_data['response_code'] == 4:
                print(f"🔄 Token exhausted, resetting...")
                if self.reset_session_token():
                    continue
                else:
                    print(f"❌ Could not reset token")
                    break
                    
            elif questions_data['response_code'] == 5:
                print(f"⏳ Rate limit reached, waiting 10 seconds...")
                time.sleep(10)
                continue
                
            else:
                print(f"❌ API error: Code {questions_data['response_code']}")
                break
        
        print(f"✅ Category '{category_name}' complete: {len(all_category_questions)} questions")
        return all_category_questions
    
    def download_complete_database(self):
        """Download the ENTIRE question database"""
        print("🚀 Starting complete download of Open Trivia DB")
        print("=" * 60)
        
        # Get global info
        global_info = self.get_global_question_count()
        if global_info:
            total_db_questions = global_info['overall']['total_num_of_verified_questions']
            print(f"🎯 Target: {total_db_questions} questions from database")
        
        # Get session token
        if not self.get_session_token():
            print("⚠️ Continuing without session token...")
        
        # Get all categories with question counts
        category_counts = self.get_category_counts()
        if not category_counts:
            print("❌ Could not get categories")
            return []
        
        total_expected = sum(cat['total_questions'] for cat in category_counts)
        print(f"\n📊 Total questions to download: {total_expected}")
        print(f"📂 Categories to process: {len(category_counts)}")
        
        all_questions = []
        processed_categories = 0
        
        # Download from each category
        for category_info in category_counts:
            processed_categories += 1
            print(f"\n📁 Processing category {processed_categories}/{len(category_counts)}")
            
            category_questions = self.download_all_questions_from_category(category_info)
            all_questions.extend(category_questions)
            
            print(f"📈 Total progress: {len(all_questions)}/{total_expected} questions")
            
            # Intermittent save every 5 categories
            if processed_categories % 5 == 0:
                self.save_backup(all_questions, f"backup_after_{processed_categories}_categories")
        
        # Download general questions (no specific category)
        print(f"\n🌐 Downloading general questions (all categories)...")
        general_questions = self.download_general_questions()
        
        print(f"\n🎉 DOWNLOAD COMPLETE!")
        print(f"📊 Total questions from categories: {len(all_questions)}")
        print(f"📊 Additional general questions: {len(general_questions)}")
        
        # Combine all questions (remove duplicates)
        combined_questions = self.remove_duplicates(all_questions + general_questions)
        
        print(f"📊 Final total (no duplicates): {len(combined_questions)}")
        
        return combined_questions
    
    def download_general_questions(self):
        """Download general questions from all categories"""
        general_questions = []
        downloaded = 0
        max_attempts = 100
        
        for attempt in range(max_attempts):
            time.sleep(self.rate_limit_delay)
            
            questions_data = self.fetch_questions_batch(amount=50)
            
            if not questions_data or questions_data['response_code'] != 0:
                if questions_data and questions_data['response_code'] == 4:
                    if self.reset_session_token():
                        continue
                break
            
            batch_questions = self.process_questions(questions_data)
            general_questions.extend(batch_questions)
            downloaded += len(batch_questions)
            
            print(f"📥 General questions: {downloaded} downloaded")
            
            if len(questions_data['results']) < 50:
                break
        
        return general_questions
    
    def remove_duplicates(self, questions):
        """Remove duplicate questions"""
        seen = set()
        unique_questions = []
        
        for question in questions:
            key = (question['question'].lower().strip(), question['correct_answer'].lower().strip())
            
            if key not in seen:
                seen.add(key)
                unique_questions.append(question)
        
        duplicates_removed = len(questions) - len(unique_questions)
        if duplicates_removed > 0:
            print(f"🗑️ Removed {duplicates_removed} duplicate questions")
        
        return unique_questions
    
    def save_backup(self, questions, suffix="backup"):
        """Save an intermittent backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trivia_{suffix}_{timestamp}.json"
        
        os.makedirs("trivia_data", exist_ok=True)
        filepath = os.path.join("trivia_data", filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Backup saved: {filepath}")
        except Exception as e:
            print(f"❌ Error saving backup: {e}")
    
    def save_complete_database(self, questions):
        """Save the complete database in the exact desired format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trivia_complete_database_{timestamp}.json"
        
        os.makedirs("trivia_data", exist_ok=True)
        filepath = os.path.join("trivia_data", filename)
        
        try:
            # Save in the exact format you specified: just the questions array
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            
            # Show a sample question to verify format
            if questions:
                print(f"\n📄 Sample question format:")
                sample = questions[0]
                print(json.dumps(sample, indent=2, ensure_ascii=False))
            
            print(f"\n🎉 COMPLETE DATABASE SAVED!")
            print(f"📁 File: {filepath}")
            print(f"📊 Total questions: {len(questions)}")
            
            # Count categories for stats
            categories = set(q['category'] for q in questions)
            print(f"📂 Categories: {len(categories)}")
            
            return filepath
        except Exception as e:
            print(f"❌ Error saving database: {e}")
            return None

def main():
    """Main function for complete download with proper encoding"""
    scraper = FastTriviaDBScraper()
    
    print("🎯 OPEN TRIVIA DB - COMPLETE DOWNLOAD (FIXED ENCODING)")
    print("=" * 60)
    print("📋 This script will download ALL available questions")
    print("🔧 FIXED: Proper URL and HTML decoding")
    print("📝 Format: Exact format you specified")
    print("⏱️ Estimated time: 30-90 minutes")
    print("🔄 Strictly respects API limits: 1 request per 5 seconds")
    print("💾 Automatic backups every 5 categories")
    
    print("\n📄 Output format:")
    print(json.dumps({
        "question": "What is the capital of France?",
        "correct_answer": "Paris",
        "incorrect_answers": ["London", "Berlin", "Madrid"],
        "category": "Geography",
        "difficulty": "easy"
    }, indent=2, ensure_ascii=False))
    
    confirm = input("\n❓ Continue with complete download? (y/n): ")
    if confirm.lower() != 'y':
        print("👋 Operation cancelled.")
        return
    
    start_time = datetime.now()
    print(f"\n🚀 Starting download at: {start_time.strftime('%H:%M:%S')}")
    
    try:
        # Download the entire database
        all_questions = scraper.download_complete_database()
        
        if all_questions:
            # Save the complete database
            filepath = scraper.save_complete_database(all_questions)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n✅ MISSION COMPLETE!")
            print(f"⏱️ Total time: {duration}")
            print(f"📊 Questions downloaded: {len(all_questions)}")
            print(f"📁 Saved to: {filepath}")
            print(f"🔧 Encoding: Fixed and properly decoded")
            
        else:
            print(f"\n❌ Could not download questions.")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Download stopped by user.")
        if hasattr(scraper, 'all_questions') and scraper.all_questions:
            print(f"💾 Saving current progress...")
            scraper.save_backup(scraper.all_questions, "interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Check dependencies
    try:
        import requests
        from urllib.parse import unquote
    except ImportError:
        print("❌ Install requests with: pip install requests")
        exit(1)
    
    main()