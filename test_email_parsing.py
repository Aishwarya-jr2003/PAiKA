import email
from email import policy
from pathlib import Path
import html2text
from datetime import datetime

def parse_eml(eml_path):
    """Parse .eml email file"""
    print("="*60)
    print(f"PARSING EMAIL: {eml_path}")
    print("="*60 + "\n")
    
    try:
        # Read the .eml file
        with open(eml_path, 'r', encoding='utf-8') as f:
            msg = email.message_from_file(f, policy=policy.default)
        
        # Extract metadata
        print("📧 EMAIL METADATA:")
        print("-"*60)
        
        from_addr = msg.get('From', 'Unknown')
        to_addr = msg.get('To', 'Unknown')
        subject = msg.get('Subject', 'No Subject')
        date = msg.get('Date', 'Unknown')
        
        print(f"From: {from_addr}")
        print(f"To: {to_addr}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print()
        
        # Extract body
        print("📝 EMAIL BODY:")
        print("-"*60)
        
        body = ""
        
        # Handle multipart emails (plain text + HTML)
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/plain':
                    body = part.get_content()
                    break
                elif content_type == 'text/html' and not body:
                    # Convert HTML to text
                    html_content = part.get_content()
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    body = h.handle(html_content)
        else:
            # Simple email
            body = msg.get_content()
        
        print(body[:500])  # Show first 500 chars
        print()
        
        # Combine into searchable format
        email_text = f"""
Email Metadata:
From: {from_addr}
To: {to_addr}
Subject: {subject}
Date: {date}

Email Body:
{body}
"""
        
        print("="*60)
        print("✅ EMAIL PARSED SUCCESSFULLY")
        print("="*60)
        print(f"Total length: {len(email_text)} characters")
        print(f"This formatted text will be stored in ChromaDB")
        print("="*60 + "\n")
        
        return email_text
        
    except Exception as e:
        print(f"❌ Error parsing email: {e}\n")
        return None

def create_sample_eml():
    """Create a sample .eml file for testing"""
    sample_eml = """From: alice@company.com
To: bob@company.com
Subject: Project Update - Q1 Goals
Date: Mon, 15 Jan 2024 10:30:00 -0500
Content-Type: text/plain; charset="utf-8"

Hi Bob,

I wanted to send you a quick update on our Q1 project goals.

Key Points:
1. We've completed the initial research phase
2. The prototype is 60% done
3. We're on track for the February launch

Next Steps:
- Schedule a review meeting for next week
- Finalize the marketing materials
- Prepare the demo for stakeholders

Let me know if you have any questions!

Best regards,
Alice
"""
    
    # Save to file
    with open('sample_email.eml', 'w', encoding='utf-8') as f:
        f.write(sample_eml)
    
    print("✅ Created sample_email.eml for testing!\n")

# Main test
if __name__ == "__main__":
    print("="*60)
    print("EMAIL PARSING TEST")
    print("="*60 + "\n")
    
    # Create sample if no .eml files exist
    eml_files = list(Path('.').glob('*.eml'))
    
    if not eml_files:
        print("📝 No .eml files found. Creating sample...\n")
        create_sample_eml()
        eml_files = ['sample_email.eml']
    
    # Test with first .eml file
    if eml_files:
        result = parse_eml(eml_files[0])
        
        if result:
            print("\n💡 THIS IS WHAT GETS STORED IN CHROMADB:")
            print("-"*60)
            print(result)
            print("-"*60)
    else:
        print("❌ No .eml files to test!")