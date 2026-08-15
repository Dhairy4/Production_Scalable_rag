import logfire 
from pypdf import PdfReader

def parse_pdf(file_path: str):
    """
    Extract text from a PDF locally using pypdf
    Falls back to pdf plumber if no text yeild (eg - image heavy pdfs)
    """

    with logfire.span("PDF Parsing", filename= file_path):
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            logfire.info(f"Total pages in PDF: {total_pages}")

            text_parts: list[str] = []
            blank_pages: list[int] = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                else:
                    blank_pages.append(i + 1)  # Store 1-based page number

            # fallback

            if blank_pages:
                logfire.warning(f"Blank pages found in PDF: {blank_pages}. Consider using pdfplumber for image-heavy PDFs.")

                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        for page_num in blank_pages:
                            page = pdf.pages[page_num - 1]
                            fallback_text = page.extract_text() or ""
                            if fallback_text.strip():
                                text_parts.append(fallback_text)


                except Exception as plum_err:
                    logfire.warning(f"No text extracted from {file_path}. File may be fully image-based.")


            full_text = "\n".join(text_parts)

            if not full_text.strip():
                logfire.warning(f"Returned empty text for file {file_path}.")
            else:
                logfire.info(f"successfully parsed {len(full_text)} characters")

            return full_text

        except Exception as e:
            logfire.error(f"Error parsing PDF file {file_path}: {e}")
            raise e