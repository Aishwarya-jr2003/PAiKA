import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import email
from email import policy
import html2text
from bs4 import BeautifulSoup
import csv
from pathlib import Path

class UniversalDocumentLoader:
    """
    Universal document loader supporting:
    - Text files (.txt, .md)
    - PDFs (.pdf)
    - Word documents (.docx)
    - Emails (.eml)
    - CSV files (.csv)
    - HTML files (.html)
    """
    
    @staticmethod
    def load_text(filepath):
        """Load plain text"""
        try:
            return open(filepath, 'r', encoding='utf-8').read()
        except:
            return open(filepath, 'r', encoding='latin-1').read()
    
    @staticmethod
    def load_pdf(filepath):
        """Load PDF with fallback"""
        # Try PyPDF2
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                if len(text.strip()) > 100:
                    return text
        except:
            pass
        
        # Fallback to pdfplumber
        with pdfplumber.open(filepath) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    
    @staticmethod
    def load_docx(filepath):
        """Load Word document"""
        doc = DocxDocument(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    
    @staticmethod
    def load_eml(filepath):
        """Load email file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            msg = email.message_from_file(f, policy=policy.default)
        
        # Extract metadata
        from_addr = msg.get('From', 'Unknown')
        to_addr = msg.get('To', 'Unknown')
        subject = msg.get('Subject', 'No Subject')
        date = msg.get('Date', 'Unknown')
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    body = part.get_content()
                    break
                elif content_type == 'text/html' and not body:
                    html_content = part.get_content()
                    h = html2text.HTML2Text()
                    body = h.handle(html_content)
        else:
            body = msg.get_content()
        
        # Format as searchable text
        return f"""Email
From: {from_addr}
To: {to_addr}
Subject: {subject}
Date: {date}

{body}"""
    
    @staticmethod
    def load_csv(filepath):
        """Load CSV and convert to searchable text"""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            text_parts = [f"CSV Data from {Path(filepath).name}\n"]
            text_parts.append(f"Columns: {', '.join(headers)}\n\n")
            
            for i, row in enumerate(reader, 1):
                row_text = f"Row {i}: "
                row_text += ", ".join([f"{k}={v}" for k, v in row.items() if v])
                text_parts.append(row_text)
            
            return "\n".join(text_parts)
    
    @staticmethod
    def load_html(filepath):
        """Load HTML and extract text"""
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)
    
    @classmethod
    def load(cls, filepath):
        """Universal loader - auto-detects and loads"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        ext = filepath.suffix.lower()
        
        loaders = {
            '.txt': cls.load_text,
            '.md': cls.load_text,
            '.pdf': cls.load_pdf,
            '.docx': cls.load_docx,
            '.eml': cls.load_eml,
            '.csv': cls.load_csv,
            '.html': cls.load_html,
            '.htm': cls.load_html
        }
        
        if ext in loaders:
            content = loaders[ext](filepath)
            return content, ext
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    @classmethod
    def get_supported_formats(cls):
        """Return list of supported formats"""
        return ['.txt', '.md', '.pdf', '.docx', '.eml', '.csv', '.html', '.htm']

# Test
if __name__ == "__main__":
    print("="*60)
    print("UNIVERSAL DOCUMENT LOADER TEST")
    print("="*60 + "\n")
    
    supported = UniversalDocumentLoader.get_supported_formats()
    print(f"📚 Supported formats: {', '.join(supported)}\n")
    
    # Find all supported files
    current_dir = Path('.')
    all_files = []
    for ext in supported:
        all_files.extend(list(current_dir.glob(f'*{ext}')))
    
    if not all_files:
        print("⚠️  No supported files found!\n")
    else:
        print(f"Found {len(all_files)} files:\n")
        
        for file in all_files:
            print(f"📄 {file.name}")
            try:
                content, file_type = UniversalDocumentLoader.load(file)
                print(f"   Type: {file_type}")
                print(f"   Length: {len(content)} characters")
                print(f"   Preview: {content[:80].replace(chr(10), ' ')}...")
                print(f"   ✅ Success!\n")
            except Exception as e:
                print(f"   ❌ Failed: {e}\n")
    
    print("="*60)
    print("✅ Universal loader ready for PAiKA!")
    print("="*60)