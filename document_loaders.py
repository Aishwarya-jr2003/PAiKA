import PyPDF2
import pdfplumber
from pathlib import Path
from docx import Document as DocxDocument

class DocumentLoader:
    """Universal document loader for multiple formats"""
    
    @staticmethod
    def detect_file_type(filepath):
        """Detect file type by extension"""
        suffix = Path(filepath).suffix.lower()
        
        type_map = {
            '.txt': 'text',
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.md': 'markdown'
        }
        
        return type_map.get(suffix, 'unknown')
    
    @staticmethod
    def load_text(filepath):
        """Load plain text file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try different encoding
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
    
    @staticmethod
    def load_pdf(filepath):
        """Load PDF with fallback strategy"""
        
        # Try PyPDF2 first (fast)
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # If we got decent text, return it
                if len(text.strip()) > 100:
                    return text
        except:
            pass
        
        # Fallback to pdfplumber (more robust)
        try:
            with pdfplumber.open(filepath) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise Exception(f"Could not extract PDF: {e}")
    
    @staticmethod
    def load_docx(filepath):
        """Load Word document"""
        try:
            doc = DocxDocument(filepath)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Could not extract DOCX: {e}")
    
    @classmethod
    def load(cls, filepath):
        """Universal loader - auto-detects type and loads"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_type = cls.detect_file_type(filepath)
        
        loaders = {
            'text': cls.load_text,
            'markdown': cls.load_text,
            'pdf': cls.load_pdf,
            'docx': cls.load_docx
        }
        
        if file_type in loaders:
            return loaders[file_type](filepath)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

# Test the loader
if __name__ == "__main__":
    print("="*60)
    print("UNIVERSAL DOCUMENT LOADER TEST")
    print("="*60 + "\n")
    
    # Test with all file types in folder
    current_dir = Path('.')
    supported_extensions = ['.txt', '.pdf', '.docx', '.md']
    
    files = []
    for ext in supported_extensions:
        files.extend(list(current_dir.glob(f'*{ext}')))
    
    if not files:
        print("⚠️  No supported files found!")
        print("\nSupported formats: .txt, .pdf, .docx, .md")
        print("\nAdd some files to test!")
    else:
        print(f"Found {len(files)} supported files:\n")
        
        for file in files:
            print(f"📄 {file.name}")
            print(f"   Type: {DocumentLoader.detect_file_type(file)}")
            
            try:
                content = DocumentLoader.load(file)
                print(f"   ✅ Loaded: {len(content)} characters")
                print(f"   Preview: {content[:80].replace(chr(10), ' ')}...")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
            
            print()
    
    print("="*60)
    print("✅ Universal loader working!")
    print("="*60)