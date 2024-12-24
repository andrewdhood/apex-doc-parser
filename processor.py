# processor.py
import pdfplumber
import re
import json
from typing import Dict, List, Optional, Union
from pathlib import Path
from patterns import PDFPatterns, ContentExtractor

class PDFDocProcessor:
    def __init__(self, debug=True):
        self.debug = debug
        self.extractor = ContentExtractor()
        self.current_page = 0

    def log(self, message: str, error=False) -> None:
        """Debug logging helper"""
        if self.debug or error:
            prefix = "ERROR" if error else "DEBUG"
            page_info = f"[Page {self.current_page}]" if self.current_page else ""
            print(f"{prefix} {page_info}: {message}")

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF with page tracking"""
        try:
            all_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                self.log(f"Processing PDF with {len(pdf.pages)} pages")
                
                for i, page in enumerate(pdf.pages):
                    self.current_page = i + 1
                    text = page.extract_text()
                    if text:
                        # Add page number markers for later reference
                        all_text += f"\n[PAGE_{i+1}]\n{text}\n[/PAGE_{i+1}]\n"
                        
            return all_text
            
        except Exception as e:
            self.log(f"Error extracting text: {str(e)}", error=True)
            return None

    def process_pdf(self, pdf_path: str) -> Dict[str, Union[str, Dict, List]]:
        """Process PDF and create structured JSON output"""
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {}

        # Create base structure
        doc = {
            "title": "",
            "description": "",
            "metadata": {
                "totalPages": self.current_page,
                "note": "In API version 51.0 and earlier, Apex Reference information was included in the Apex Developer Guide"
            },
            "sections": [],
            "dmlOperations": {}
        }

        # Extract title and description
        title_match = re.search(PDFPatterns.TITLE, text)
        if title_match:
            doc["title"] = title_match.group(0)

        desc_match = re.search(PDFPatterns.MAIN_DESC, text, re.DOTALL)
        if desc_match:
            doc["description"] = desc_match.group(0)

        # Extract namespaces
        doc["sections"] = self.extractor.extract_namespaces(text)

        # Extract DML operations
        doc["dmlOperations"] = self.extractor.extract_dml_operations(text)

        return doc

    def save_json(self, data: Dict, output_path: str) -> None:
        """Save the JSON data to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        self.log(f"Saved JSON to: {output_path}")