from pathlib import Path
import re
import json
from typing import Dict, List, Union

class ApexDocParser:
    """Parser to extract and organize Apex Reference Guide content into structured JSON."""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def parse_document(self, text: str) -> Dict[str, Union[str, List[Dict]]]:
        """Parse the Apex Reference Guide content."""
        if self.debug:
            print("Starting document parsing...")

        namespaces = self.extract_namespaces(text)
        
        return {
            "title": "Apex Reference Guide",
            "description": "Extracted Apex content organized by namespaces.",
            "namespaces": namespaces
        }

    def extract_namespaces(self, text: str) -> List[Dict[str, Union[str, List]]]:
        """Extract namespaces and their classes, methods, and descriptions."""
        namespace_pattern = re.compile(r"^(\w+)\s+Namespace", re.MULTILINE)
        class_pattern = re.compile(r"^(\w+)\s+Class", re.MULTILINE)
        method_pattern = re.compile(r"^(public|private|protected)\s+\w+\s+\w+\(.*\)")
        
        namespaces = []
        
        for match in namespace_pattern.finditer(text):
            namespace = {
                "name": match.group(1),
                "description": self.extract_section_description(text, match.end()),
                "classes": []
            }
            
            class_matches = class_pattern.finditer(text, match.end())
            for class_match in class_matches:
                class_def = {
                    "name": class_match.group(1),
                    "description": self.extract_section_description(text, class_match.end()),
                    "methods": []
                }
                
                method_matches = method_pattern.finditer(text, class_match.end())
                for method_match in method_matches:
                    method_def = {
                        "signature": method_match.group(0),
                        "description": self.extract_section_description(text, method_match.end())
                    }
                    class_def["methods"].append(method_def)
                namespace["classes"].append(class_def)

                # Break the loop if encountering a new namespace
                if namespace_pattern.search(text, class_match.end()):
                    break
            
            namespaces.append(namespace)
        
        return namespaces

    def extract_section_description(self, text: str, start_pos: int) -> str:
        """Extract the section description immediately following a match."""
        end_pos = text.find("\n\n", start_pos)
        return text[start_pos:end_pos].strip() if end_pos != -1 else text[start_pos:].strip()

    def save_to_json(self, data: Dict, output_path: str):
        """Save the parsed content to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_path = Path("apex_reference.txt")
    output_path = Path("apex_reference.json")

    if input_path.exists():
        with open(input_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        parser = ApexDocParser(debug=True)
        parsed_data = parser.parse_document(text_content)
        parser.save_to_json(parsed_data, output_path)

        print(f"Parsing complete. Output saved to {output_path}")
    else:
        print(f"Input file {input_path} does not exist.")