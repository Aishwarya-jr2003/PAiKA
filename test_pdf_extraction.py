import PyPDF2
import pdfplumber
from pathlib import Path

def extract_with_pypdf2(pdf_path):
    """Method 1: PyPDF2 (fast, simple)"""
    print(f"📄 Trying PyPDF2 on: {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            print(f"   Pages: {len(reader.pages)}")
            
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += page_text
                
                # Show preview of first page
                if i == 0:
                    preview = page_text[:200].replace('\n', ' ')
                    print(f"   Page 1 preview: {preview}...")
            
            print(f"   Total extracted: {len(text)} characters")
            print(f"   ✅ PyPDF2 SUCCESS\n")
            return text
            
    except Exception as e:
        print(f"   ❌ PyPDF2 FAILED: {e}\n")
        return None

def extract_with_pdfplumber(pdf_path):
    """Method 2: pdfplumber (more robust)"""
    print(f"📄 Trying pdfplumber on: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"   Pages: {len(pdf.pages)}")
            
            text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                
                # Show preview of first page
                if i == 0 and page_text:
                    preview = page_text[:200].replace('\n', ' ')
                    print(f"   Page 1 preview: {preview}...")
            
            print(f"   Total extracted: {len(text)} characters")
            print(f"   ✅ pdfplumber SUCCESS\n")
            return text
            
    except Exception as e:
        print(f"   ❌ pdfplumber FAILED: {e}\n")
        return None

def smart_pdf_extract(pdf_path):
    """Smart extraction with fallback"""
    print("="*60)
    print(f"SMART PDF EXTRACTION")
    print("="*60 + "\n")
    
    # Try PyPDF2 first (faster)
    text = extract_with_pypdf2(pdf_path)
    
    # If PyPDF2 fails or gets very little text, try pdfplumber
    if not text or len(text) < 100:
        print("⚠️  PyPDF2 didn't get much text, trying pdfplumber...\n")
        text = extract_with_pdfplumber(pdf_path)
    
    if text and len(text) > 100:
        print("="*60)
        print("✅ EXTRACTION SUCCESSFUL!")
        print("="*60)
        print(f"Total text: {len(text)} characters")
        print(f"Words: ~{len(text.split())} words")
        return text
    else:
        print("="*60)
        print("❌ EXTRACTION FAILED")
        print("="*60)
        print("This might be an image-based PDF (scanned document)")
        print("Would need OCR to extract text")
        return None

# Test with any PDF file you have
print("="*60)
print("PDF EXTRACTION TESTER")
print("="*60 + "\n")

print("Instructions:")
print("1. Place a PDF file in the PAiKA folder")
print("2. Enter the filename below")
print("3. We'll test both extraction methods\n")

pdf_file = input("Enter PDF filename (e.g., document.pdf): ").strip()

if Path(pdf_file).exists():
    result = smart_pdf_extract(pdf_file)
    
    if result:
        print(f"\n📝 First 500 characters of extracted text:")
        print("-"*60)
        print(result[:500])
        print("-"*60)
else:
    print(f"\n❌ File not found: {pdf_file}")
    print("\nFor testing, you can:")
    print("1. Download any PDF from the internet")
    print("2. Create a PDF from a Word document")
    print("3. Save a web page as PDF")
    print("\nThen run this script again!")