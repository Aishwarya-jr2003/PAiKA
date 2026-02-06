import csv
from pathlib import Path

def parse_csv_to_text(csv_path):
    """Convert CSV to searchable text"""
    print("="*60)
    print(f"PARSING CSV: {csv_path}")
    print("="*60 + "\n")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Get headers
            headers = reader.fieldnames
            print(f"📊 Columns: {', '.join(headers)}\n")
            
            # Convert rows to text
            text_parts = [f"CSV File: {Path(csv_path).name}\n"]
            text_parts.append(f"Columns: {', '.join(headers)}\n\n")
            
            row_count = 0
            for row in reader:
                row_count += 1
                # Each row becomes a sentence
                row_text = f"Row {row_count}: "
                row_text += ", ".join([f"{k}={v}" for k, v in row.items() if v])
                text_parts.append(row_text)
            
            full_text = "\n".join(text_parts)
            
            print("📝 CONVERTED TO TEXT:")
            print("-"*60)
            print(full_text[:500])  # Preview
            print("-"*60)
            print(f"\n✅ Converted {row_count} rows to searchable text")
            print(f"Total length: {len(full_text)} characters\n")
            
            return full_text
            
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}\n")
        return None

def create_sample_csv():
    """Create a sample CSV for testing"""
    sample_data = """Name,Role,Department,Email
Alice Johnson,Senior Developer,Engineering,alice@company.com
Bob Smith,Product Manager,Product,bob@company.com
Carol White,Designer,Design,carol@company.com
David Brown,Data Scientist,Analytics,david@company.com
Eve Davis,Marketing Lead,Marketing,eve@company.com
"""
    
    with open('sample_employees.csv', 'w') as f:
        f.write(sample_data)
    
    print("✅ Created sample_employees.csv for testing!\n")

# Test
if __name__ == "__main__":
    print("="*60)
    print("CSV PARSING TEST")
    print("="*60 + "\n")
    
    # Create sample if needed
    csv_files = list(Path('.').glob('*.csv'))
    
    if not csv_files:
        print("📝 Creating sample CSV...\n")
        create_sample_csv()
        csv_files = ['sample_employees.csv']
    
    # Test
    if csv_files:
        result = parse_csv_to_text(csv_files[0])
        
        if result:
            print("\n💡 SEARCHABLE IN CHROMADB:")
            print("You can now ask:")
            print("  - 'Who works in Engineering?'")
            print("  - 'What is Alice's email?'")
            print("  - 'List all developers'")