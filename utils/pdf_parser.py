import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path, max_pages=100):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                if page.number >= max_pages:  # Safety limit
                    break
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text
