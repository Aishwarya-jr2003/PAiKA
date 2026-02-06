import PyPDF2
import pdfplumber
from pathlib import Path


def analyze_pdf(pdf_path):
    """Comprehensive PDF analysis"""

    print("=" * 60)
    print(f"ANALYZING: {pdf_path}")
    print("=" * 60 + "\n")

    if not Path(pdf_path).exists():
        print("❌ File not found!")
        return

    first_page_text = ""
    has_tables = False
    has_images = False

    # --------------------------------------------------
    # BASIC INFO (PyPDF2)
    # --------------------------------------------------
    print("📊 BASIC INFO:")
    print("-" * 60)

    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)

            print(f"Pages: {len(reader.pages)}")

            # Metadata
            if reader.metadata:
                print("\nMetadata:")
                for key, value in reader.metadata.items():
                    print(f"  {key}: {value}")

            # Encryption check
            if reader.is_encrypted:
                print("\n⚠️ PDF is ENCRYPTED – may need password")

            # First page text check
            first_page_text = reader.pages[0].extract_text() or ""

            if len(first_page_text.strip()) < 50:
                print("\n⚠️ Very little text extracted")
                print("   Likely scanned / image-based PDF")
                print("   OCR may be required")
            else:
                print("\n✅ Text extraction looks good")
                print(f"   First page length: {len(first_page_text)} characters")

    except Exception as e:
        print(f"❌ PyPDF2 Error: {e}")

    # --------------------------------------------------
    # DETAILED ANALYSIS (pdfplumber)
    # --------------------------------------------------
    print("\n" + "=" * 60)
    print("📄 DETAILED ANALYSIS (pdfplumber)")
    print("-" * 60)

    try:
        total_text = 0

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    total_text += len(page_text)

                # Tables
                if page.extract_tables():
                    has_tables = True

                # Images
                if page.images:
                    has_images = True

        print(f"Total extracted text: {total_text} characters")
        print(f"Contains tables: {'Yes' if has_tables else 'No'}")
        print(f"Contains images: {'Yes' if has_images else 'No'}")

        if has_tables:
            print("\n📊 Tables detected – pdfplumber is suitable")

        if has_images:
            print("\n🖼️ Images detected – OCR needed for image text")

    except Exception as e:
        print(f"❌ pdfplumber Error: {e}")

    # --------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)

    if first_page_text and len(first_page_text.strip()) > 100:
        print("✅ Use PyPDF2 or pdfplumber – text-based PDF")
    elif has_tables:
        print("✅ Prefer pdfplumber – better table extraction")
    else:
        print("⚠️ Consider OCR (Tesseract) – scanned document")

    print("=" * 60 + "\n")


# --------------------------------------------------
# Main entry point
# --------------------------------------------------
if __name__ == "__main__":
    pdf_file = input("Enter PDF filename to analyze: ").strip()

    if pdf_file:
        analyze_pdf(pdf_file)
    else:
        print("❌ No file specified!")
