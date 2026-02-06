from bs4 import BeautifulSoup
import html2text
from pathlib import Path

def parse_html_to_text(html_path):
    """Convert HTML to clean text"""
    print("="*60)
    print(f"PARSING HTML: {html_path}")
    print("="*60 + "\n")
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Method 1: BeautifulSoup (cleaner)
        print("METHOD 1: BeautifulSoup (Extract text only)")
        print("-"*60)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_bs = '\n'.join(chunk for chunk in chunks if chunk)
        
        print(text_bs[:300])
        print()
        
        # Method 2: html2text (Preserves some structure)
        print("METHOD 2: html2text (Preserves structure)")
        print("-"*60)
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        text_h2t = h.handle(html_content)
        
        print(text_h2t[:300])
        print()
        
        print("="*60)
        print("✅ HTML PARSED")
        print("="*60)
        print(f"BeautifulSoup length: {len(text_bs)} chars")
        print(f"html2text length: {len(text_h2t)} chars")
        print("\nRecommendation: Use BeautifulSoup for cleaner text")
        print("="*60 + "\n")
        
        return text_bs
        
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}\n")
        return None

def create_sample_html():
    """Create sample HTML file"""
    sample_html = """<!DOCTYPE html>
<html>
<head>
    <title>Company Meeting Notes</title>
</head>
<body>
    <h1>Q1 Strategy Meeting - January 15, 2024</h1>
    
    <h2>Attendees</h2>
    <ul>
        <li>Alice Johnson - Engineering Lead</li>
        <li>Bob Smith - Product Manager</li>
        <li>Carol White - Design Lead</li>
    </ul>
    
    <h2>Key Discussion Points</h2>
    <p>We discussed the following items for Q1 2024:</p>
    
    <h3>1. Product Roadmap</h3>
    <p>The team agreed to prioritize the following features:</p>
    <ul>
        <li>User dashboard redesign</li>
        <li>Mobile app improvements</li>
        <li>API performance optimization</li>
    </ul>
    
    <h3>2. Resource Allocation</h3>
    <p>We need to hire 3 additional engineers by March to meet our goals.</p>
    
    <h3>3. Timeline</h3>
    <p>Launch target: End of Q1 (March 31, 2024)</p>
    
    <h2>Action Items</h2>
    <ol>
        <li>Alice: Complete technical specs by Jan 20</li>
        <li>Bob: Schedule user research sessions</li>
        <li>Carol: Prepare design mockups by Jan 25</li>
    </ol>
</body>
</html>
"""
    
    with open('sample_meeting_notes.html', 'w', encoding='utf-8') as f:
        f.write(sample_html)
    
    print("✅ Created sample_meeting_notes.html for testing!\n")

# Test
if __name__ == "__main__":
    # Need to install beautifulsoup4
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installing BeautifulSoup4...")
        import os
        os.system("pip install beautifulsoup4")
        from bs4 import BeautifulSoup
    
    print("="*60)
    print("HTML PARSING TEST")
    print("="*60 + "\n")
    
    html_files = list(Path('.').glob('*.html'))
    
    if not html_files:
        print("📝 Creating sample HTML...\n")
        create_sample_html()
        html_files = ['sample_meeting_notes.html']
    
    if html_files:
        result = parse_html_to_text(html_files[0])