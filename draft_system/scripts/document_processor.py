#!/usr/bin/env python3
"""
Document Processing System for Draft Agent
Handles PDF parsing, OCR fallback, and document organization
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import mimetypes

# Document processing imports (install with: pip install PyPDF2 pytesseract pillow pdf2image)
try:
    import PyPDF2
    import pytesseract
    from PIL import Image
    import pdf2image
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False
    print("Warning: Document processing libraries not installed.")
    print("Install with: pip install PyPDF2 pytesseract pillow pdf2image")

class DocumentProcessor:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for document processing"""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "document_processing.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def identify_document_type(self, file_path):
        """Identify document type based on file extension and content"""
        file_path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if mime_type:
            if mime_type.startswith('application/pdf'):
                return 'pdf'
            elif mime_type.startswith('image/'):
                return 'image'
            elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return 'word'
            elif mime_type.startswith('text/'):
                return 'text'
        
        # Fallback to extension-based detection
        ext = file_path.suffix.lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return 'image'
        elif ext in ['.doc', '.docx']:
            return 'word'
        elif ext in ['.txt', '.md']:
            return 'text'
        else:
            return 'unknown'
    
    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF using PyPDF2"""
        if not PROCESSING_AVAILABLE:
            return None, "Processing libraries not available"
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Check if extraction was successful
                if len(text.strip()) < 100:
                    return None, "Insufficient text extracted, may be scanned PDF"
                
                return text, "success"
        except Exception as e:
            return None, f"PDF extraction failed: {str(e)}"
    
    def ocr_pdf(self, pdf_path):
        """Extract text from PDF using OCR (fallback method)"""
        if not PROCESSING_AVAILABLE:
            return None, "OCR libraries not available"
        
        try:
            pages = pdf2image.convert_from_path(pdf_path)
            text = ""
            for i, page in enumerate(pages):
                page_text = pytesseract.image_to_string(page)
                text += f"--- Page {i+1} ---\n{page_text}\n\n"
            
            return text, "success"
        except Exception as e:
            return None, f"OCR processing failed: {str(e)}"
    
    def process_image(self, image_path):
        """Extract text from image using OCR"""
        if not PROCESSING_AVAILABLE:
            return None, "OCR libraries not available"
        
        try:
            image = Image.open(image_path)
            # Preprocessing for better OCR results
            image = image.convert('L')  # Convert to grayscale
            text = pytesseract.image_to_string(image)
            return text, "success"
        except Exception as e:
            return None, f"Image OCR failed: {str(e)}"
    
    def process_text_file(self, file_path):
        """Read text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text, "success"
        except Exception as e:
            return None, f"Text file reading failed: {str(e)}"
    
    def classify_document(self, file_path, extracted_text):
        """Classify document based on content and filename"""
        filename = Path(file_path).name.lower()
        text_lower = extracted_text.lower() if extracted_text else ""
        
        # Legal document indicators
        legal_keywords = ['complaint', 'motion', 'order', 'judgment', 'contract', 'agreement', 'pleading']
        evidence_keywords = ['receipt', 'invoice', 'statement', 'record', 'correspondence', 'email']
        research_keywords = ['case law', 'statute', 'regulation', 'opinion', 'holding']
        
        if any(keyword in filename or keyword in text_lower for keyword in legal_keywords):
            return 'legal_document'
        elif any(keyword in filename or keyword in text_lower for keyword in evidence_keywords):
            return 'evidence'
        elif any(keyword in filename or keyword in text_lower for keyword in research_keywords):
            return 'research'
        else:
            return 'administrative'
    
    def determine_destination(self, classification, file_path):
        """Determine where processed document should be stored"""
        base_name = Path(file_path).stem
        
        if classification == 'legal_document':
            # Check if there's a relevant active draft
            active_drafts = self.base_dir / "active_drafts"
            if active_drafts.exists():
                # For now, put in exhibits_master, but could be more sophisticated
                return self.base_dir / "exhibits_master"
            else:
                return self.base_dir / "exhibits_master"
        elif classification == 'evidence':
            return self.base_dir / "exhibits_master"
        elif classification == 'research':
            return self.base_dir / "case_resources" / "case_law"
        else:
            return self.base_dir / "Intake" / "preliminary_docs" / "processed"
    
    def create_summary_file(self, original_path, extracted_text, classification, destination):
        """Create summary markdown file for processed document"""
        original_path = Path(original_path)
        base_name = original_path.stem
        summary_path = destination / f"{base_name}_summary.md"
        
        # Analyze text for key information
        key_info = self.extract_key_information(extracted_text, classification)
        
        summary_content = f"""# Document Summary: {original_path.name}

## Document Information
- **Original Filename**: {original_path.name}
- **Document Type**: {classification.replace('_', ' ').title()}
- **Processing Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Processing Method**: {"OCR" if "OCR" in str(extracted_text) else "Text Extraction"}

## Content Summary
{key_info.get('summary', 'Document processed and text extracted.')}

## Legal Relevance
{key_info.get('relevance', 'To be determined based on case context.')}

## Key Information Extracted
- **Length**: {len(extracted_text) if extracted_text else 0} characters
- **Estimated Pages**: {max(1, len(extracted_text) // 2000) if extracted_text else 'Unknown'}

## Recommended Actions
- [ ] Review extracted text for accuracy
- [ ] Determine specific legal relevance
- [ ] Cross-reference with case documents
- [ ] Consider authentication requirements

## Processing Notes
- File processed on {datetime.now().strftime('%Y-%m-%d')}
- Classification: {classification}
- Destination: {destination}
"""
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return summary_path
    
    def extract_key_information(self, text, classification):
        """Extract key information from document text"""
        if not text:
            return {'summary': 'No text could be extracted from document.', 'relevance': 'Unknown'}
        
        # Simple analysis - could be enhanced with NLP
        words = text.split()
        sentences = text.split('.')
        
        summary = f"Document contains approximately {len(words)} words across {len(sentences)} sentences."
        
        if classification == 'legal_document':
            relevance = "Appears to be a legal document that may contain important case information."
        elif classification == 'evidence':
            relevance = "Appears to be evidence that may support legal arguments."
        else:
            relevance = "Document classification suggests administrative or research material."
        
        return {'summary': summary, 'relevance': relevance}
    
    def process_document(self, file_path, destination=None):
        """Main document processing function"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
        
        self.logger.info(f"Processing document: {file_path}")
        
        # Step 1: Identify document type
        doc_type = self.identify_document_type(file_path)
        self.logger.info(f"Document type identified: {doc_type}")
        
        # Step 2: Extract text based on document type
        extracted_text = None
        processing_method = None
        
        if doc_type == 'pdf':
            # Try PDF text extraction first
            extracted_text, result = self.extract_pdf_text(file_path)
            if extracted_text:
                processing_method = "PDF Text Extraction"
            else:
                # Fallback to OCR
                self.logger.info("PDF text extraction failed, trying OCR...")
                extracted_text, result = self.ocr_pdf(file_path)
                processing_method = "OCR"
        elif doc_type == 'image':
            extracted_text, result = self.process_image(file_path)
            processing_method = "OCR"
        elif doc_type == 'text':
            extracted_text, result = self.process_text_file(file_path)
            processing_method = "Direct Text Reading"
        else:
            self.logger.warning(f"Unsupported document type: {doc_type}")
            return False
        
        if not extracted_text:
            self.logger.error(f"Text extraction failed: {result}")
            return False
        
        # Step 3: Classify document
        classification = self.classify_document(file_path, extracted_text)
        self.logger.info(f"Document classified as: {classification}")
        
        # Step 4: Determine destination
        if not destination:
            destination = self.determine_destination(classification, file_path)
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        
        # Step 5: Create three-file system
        base_name = file_path.stem
        
        # 1. Copy original file
        original_dest = destination / f"{base_name}_original{file_path.suffix}"
        import shutil
        shutil.copy2(file_path, original_dest)
        
        # 2. Save extracted text
        text_dest = destination / f"{base_name}_text.txt"
        with open(text_dest, 'w', encoding='utf-8') as f:
            f.write(f"Processing Method: {processing_method}\n")
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(extracted_text)
        
        # 3. Create summary file
        summary_dest = self.create_summary_file(file_path, extracted_text, classification, destination)
        
        self.logger.info(f"Document processing completed:")
        self.logger.info(f"  Original: {original_dest}")
        self.logger.info(f"  Text: {text_dest}")
        self.logger.info(f"  Summary: {summary_dest}")
        
        return True

def main():
    """Command line interface for document processing"""
    if len(sys.argv) < 2:
        print("Usage: python document_processor.py <file_path> [destination_folder]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    destination = sys.argv[2] if len(sys.argv) > 2 else None
    
    processor = DocumentProcessor()
    success = processor.process_document(file_path, destination)
    
    if success:
        print("Document processing completed successfully!")
    else:
        print("Document processing failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
