import json
import os
import math
from datetime import datetime

class JSONSplitter:
    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size
        
    def split_json_file(self, input_filename, output_folder=None):
        """Split a large JSON file into smaller chunks"""
        
        # Set default output folder
        if not output_folder:
            base_name = os.path.splitext(os.path.basename(input_filename))[0]
            output_folder = f"{base_name}_chunks"
        
        print(f"🔄 Splitting {input_filename} into chunks of {self.chunk_size}")
        print(f"📁 Output folder: {output_folder}")
        print("=" * 60)
        
        # Load the JSON file
        try:
            with open(input_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data)} objects from JSON")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False
        
        # Validate that it's a list
        if not isinstance(data, list):
            print("❌ JSON must contain a list of objects")
            return False
        
        if len(data) == 0:
            print("❌ JSON file is empty")
            return False
        
        # Calculate number of chunks needed
        total_chunks = math.ceil(len(data) / self.chunk_size)
        print(f"📊 Will create {total_chunks} chunks")
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Split into chunks
        successful_chunks = 0
        
        for chunk_index in range(total_chunks):
            try:
                # Calculate start and end indices
                start_idx = chunk_index * self.chunk_size
                end_idx = min(start_idx + self.chunk_size, len(data))
                
                # Extract chunk
                chunk_data = data[start_idx:end_idx]
                chunk_size_actual = len(chunk_data)
                
                # Create filename with zero-padded numbers
                chunk_filename = f"chunk_{chunk_index + 1:03d}_of_{total_chunks:03d}.json"
                chunk_path = os.path.join(output_folder, chunk_filename)
                
                # Save chunk
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                
                successful_chunks += 1
                percentage = ((chunk_index + 1) / total_chunks) * 100
                
                print(f"✅ Chunk {chunk_index + 1}/{total_chunks} ({percentage:.1f}%): {chunk_size_actual} objects → {chunk_filename}")
                
                # Show sample from first chunk
                if chunk_index == 0 and chunk_data:
                    print(f"\n📄 Sample from first chunk:")
                    sample = chunk_data[0]
                    # Show only first few fields to avoid clutter
                    sample_preview = {
                        "question": sample.get("question", "")[:100] + ("..." if len(sample.get("question", "")) > 100 else ""),
                        "correct_answer": sample.get("correct_answer", ""),
                        "category": sample.get("category", ""),
                        "difficulty": sample.get("difficulty", "")
                    }
                    print(json.dumps(sample_preview, indent=2, ensure_ascii=False))
                    print()
                
            except Exception as e:
                print(f"❌ Error creating chunk {chunk_index + 1}: {e}")
                continue
        
        # Summary
        print(f"\n🎉 SPLITTING COMPLETE!")
        print(f"📊 Original file: {len(data)} objects")
        print(f"📁 Created: {successful_chunks}/{total_chunks} chunks")
        print(f"📂 Output folder: {output_folder}")
        print(f"💾 Chunk size: {self.chunk_size} objects each")
        
        # List all created files
        print(f"\n📋 Created files:")
        try:
            chunk_files = sorted([f for f in os.listdir(output_folder) if f.endswith('.json')])
            for i, filename in enumerate(chunk_files, 1):
                filepath = os.path.join(output_folder, filename)
                file_size = os.path.getsize(filepath)
                file_size_mb = file_size / (1024 * 1024)
                print(f"   {i:2d}. {filename} ({file_size_mb:.1f} MB)")
        except Exception as e:
            print(f"⚠️ Could not list files: {e}")
        
        return successful_chunks == total_chunks
    
    def get_file_info(self, filename):
        """Get information about a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                total_objects = len(data)
                chunks_needed = math.ceil(total_objects / self.chunk_size)
                
                print(f"📊 File Analysis: {filename}")
                print(f"   📦 Total objects: {total_objects}")
                print(f"   🔢 Chunks needed: {chunks_needed}")
                print(f"   📏 Chunk size: {self.chunk_size}")
                
                # Show sample object structure
                if data:
                    print(f"   📋 Object structure:")
                    sample = data[0]
                    for key, value in sample.items():
                        value_preview = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
                        print(f"      • {key}: {value_preview}")
                
                return True
            else:
                print(f"❌ File is not a JSON array")
                return False
                
        except Exception as e:
            print(f"❌ Error analyzing file: {e}")
            return False

def main():
    print("✂️  JSON SPLITTER - Împarte JSON-ul în bucăți")
    print("=" * 60)
    print("📋 Acest script împarte un JSON mare în fichiere mai mici")
    print("🎯 Dimensiune implicită: 1000 obiecte per chunk")
    print("📁 Creează un folder nou cu toate bucățile")
    
    # Get input file
    input_file = input("\n📁 Introdu calea către fișierul JSON: ").strip()
    input_file = input_file.strip('"')  # Remove quotes if present
    
    if not os.path.exists(input_file):
        print(f"❌ Fișierul nu a fost găsit: {input_file}")
        return
    
    # Get chunk size
    chunk_size_input = input(f"📦 Dimensiunea chunk-ului (apasă Enter pentru 1000): ").strip()
    
    try:
        chunk_size = int(chunk_size_input) if chunk_size_input else 1000
        if chunk_size <= 0:
            print("❌ Dimensiunea chunk-ului trebuie să fie pozitivă")
            return
    except ValueError:
        print("❌ Dimensiunea chunk-ului trebuie să fie un număr")
        return
    
    # Optional output folder
    output_folder = input("📁 Folder de output (apasă Enter pentru auto): ").strip()
    if not output_folder:
        output_folder = None
    
    # Create splitter
    splitter = JSONSplitter(chunk_size=chunk_size)
    
    # Show file info first
    print(f"\n🔍 Analizez fișierul...")
    if not splitter.get_file_info(input_file):
        return
    
    print(f"\n📋 Setări:")
    print(f"   📥 Input: {input_file}")
    print(f"   📤 Output: {output_folder or 'Auto-generat'}")
    print(f"   📦 Dimensiune chunk: {chunk_size} obiecte")
    
    confirm = input("\n❓ Începi împărțirea? (y/n): ")
    if confirm.lower() != 'y':
        print("👋 Operația a fost anulată.")
        return
    
    # Start splitting
    success = splitter.split_json_file(input_file, output_folder)
    
    if success:
        print(f"\n✅ Împărțirea s-a finalizat cu succes!")
        print(f"🎯 JSON-ul tău a fost împărțit în bucăți de {chunk_size} obiecte!")
    else:
        print(f"\n❌ Împărțirea nu s-a finalizat complet.")

if __name__ == "__main__":
    main()