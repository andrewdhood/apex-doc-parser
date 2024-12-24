import re
from typing import Dict, List, Optional, Union

class PDFPatterns:
    """Define improved patterns for extracting content from the Apex Reference Guide"""

    # Main document structure
    TITLE = r'APEX\s+REFERENCE\s+GUIDE'
    MAIN_DESC = r'Apex is a strongly typed.*?(?=\n\n)'

    # Namespace patterns
    NAMESPACE_START = r'^([A-Z][a-zA-Z]+)\s+Namespace\s*$'
    NAMESPACE_DESC = r'(?<=Namespace\n)(.*?)(?=\n\n|\n[A-Z])'

    # DML Operation patterns
    DML_OPERATION = {
        'start': r'^([A-Z][a-zA-Z]+)\s+Statement\s*$',
        'syntax': r'Syntax\s*\n(.*?)(?=\n\n)',
        'description': r'(?<=Statement\n)(.*?)(?=Syntax)',
        'example': r'Example\s*\n(.*?)(?=\n\n(?:[A-Z]|\Z))'
    }

    # Class patterns
    CLASS_START = r'^([A-Z][a-zA-Z]+)\s+Class\s*$'
    CLASS_DESC = r'Class\s+(.*?)(?=\n(?:IN THIS SECTION:|SEE ALSO:|public|private|protected))'

    # Method patterns
    METHOD_START = r'^(?:public|private|protected)\s+\w+\s+\w+\s*\('
    METHOD_DESC = r'(?:Signature\n.*?\nReturn Value\nType:.*?\n)(.*?)(?=\n(?:Example|Usage|SEE ALSO))'

    # Section markers
    SECTION_MARKERS = [
        'IN THIS SECTION:',
        'SEE ALSO:',
        'Usage',
        'Example'
    ]

    # Content delimiters 
    CODE_BLOCK = r'```.*?```'
    NOTE_BLOCK = r'Note:.*?\n'

class ContentExtractor:
    """Extract and structure content from PDF text"""

    def __init__(self, patterns: PDFPatterns = PDFPatterns):
        self.patterns = patterns
        self.current_page = 0
        self.debug = True

    def clean_description(self, text: str) -> str:
        """Clean unwanted markers, symbols, and excessive newlines from the description."""
        # Remove known markers and page numbers
        text = re.sub(r'IN THIS SECTION:|SEE ALSO:', '', text)
        text = re.sub(r'\[PAGE_\d+\]', '', text)
        # Normalize multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        return text


    def extract_dml_operations(self, text: str) -> Dict[str, List[Dict[str, Union[str, List[str]]]]]:
        """Extract DML operations with improved syntax and example handling."""
        operations = {'statements': []}

        # Find all DML operation sections
        operation_matches = re.finditer(self.patterns.DML_OPERATION['start'], text, re.MULTILINE)

        for match in operation_matches:
            operation = {
                'name': match.group(1) + ' Statement',
                'description': '',
                'syntax': [],
                'example': ''
            }

            # Get operation content
            start_pos = match.start()
            next_match = re.search(self.patterns.DML_OPERATION['start'], text[start_pos + 1:])
            end_pos = next_match.start() + start_pos if next_match else len(text)
            operation_content = text[start_pos:end_pos]

            # Extract components
            syntax_match = re.search(self.patterns.DML_OPERATION['syntax'], operation_content, re.DOTALL)
            if syntax_match:
                operation['syntax'] = [s.strip() for s in syntax_match.group(1).split('\n') if s.strip()]

            desc_match = re.search(self.patterns.DML_OPERATION['description'], operation_content, re.DOTALL)
            if desc_match:
                operation['description'] = desc_match.group(1).strip()

            example_match = re.search(self.patterns.DML_OPERATION['example'], operation_content, re.DOTALL)
            if example_match:
                operation['example'] = example_match.group(1).strip()

            operations['statements'].append(operation)

        return operations

    def extract_namespaces(self, text: str) -> List[Dict[str, Union[str, List, Dict[str, int]]]]:
        """Extract namespace sections with improved context awareness"""
        namespaces = []

        # Find all namespace sections
        namespace_matches = re.finditer(self.patterns.NAMESPACE_START, text, re.MULTILINE)

        for match in namespace_matches:
            namespace = {
                'name': match.group(1),
                'description': '',
                'subsections': [],
                'pageRange': {'start': 0, 'end': 0}
            }

            # Get section content
            start_pos = match.start()
            next_match = re.search(self.patterns.NAMESPACE_START, text[start_pos + 1:])
            end_pos = next_match.start() + start_pos if next_match else len(text)
            section_content = text[start_pos:end_pos]

            # Extract description
            desc_match = re.search(self.patterns.NAMESPACE_DESC, section_content, re.DOTALL)
            if desc_match:
                namespace['description'] = self.clean_description(desc_match.group(1).strip())

            # Extract classes
            classes = self.extract_classes(section_content)
            namespace['subsections'].extend(classes)

            # Find page numbers
            namespace['pageRange'] = self.find_page_range(section_content)

            namespaces.append(namespace)

        return namespaces

    def find_page_range(self, content: str) -> Dict[str, int]:
        """Find page range for a section of content"""
        start_match = re.search(r'\[PAGE_(\d+)\]', content)
        end_match = re.search(r'\[/PAGE_(\d+)\](?!.*\[/PAGE_\d+\])', content)

        return {
            'start': int(start_match.group(1)) if start_match else 0,
            'end': int(end_match.group(1)) if end_match else 0
        }

    def extract_classes(self, text: str) -> List[Dict[str, Union[str, List]]]:
        """Extract class information with improved method detection"""
        classes = []

        # Find all class definitions
        class_matches = re.finditer(self.patterns.CLASS_START, text, re.MULTILINE)

        for match in class_matches:
            class_info = {
                'name': match.group(1) + ' Class',
                'description': '',
                'methods': []
            }

            # Get class content
            start_pos = match.start()
            next_match = re.search(self.patterns.CLASS_START, text[start_pos + 1:])
            end_pos = next_match.start() + start_pos if next_match else len(text)
            class_content = text[start_pos:end_pos]

            # Extract description
            desc_match = re.search(self.patterns.CLASS_DESC, class_content, re.DOTALL)
            if desc_match:
                class_info['description'] = self.clean_description(desc_match.group(1).strip())

            # Extract methods
            methods = self.extract_methods(class_content)
            class_info['methods'].extend(methods)

            classes.append(class_info)

        return classes

    def extract_methods(self, text: str) -> List[Dict[str, Union[str, List[str]]]]:
        """Extract method information with signature and parameter parsing."""
        methods = []

        # Find all method definitions
        method_matches = re.finditer(self.patterns.METHOD_START, text, re.MULTILINE)

        for match in method_matches:
            method = {
                'name': '',
                'signature': '',
                'description': '',
                'parameters': [],
                'return_type': ''
            }

            # Get method content
            start_pos = match.start()
            next_match = re.search(self.patterns.METHOD_START, text[start_pos + 1:])
            end_pos = next_match.start() + start_pos if next_match else len(text)
            method_content = text[start_pos:end_pos]

            # Parse signature
            signature_lines = method_content.split('\n')[0]
            method['signature'] = signature_lines.strip()

            # Extract method name
            name_match = re.search(r'\w+\s*\(', signature_lines)
            if name_match:
                method['name'] = name_match.group(0)[:-1].strip()

            # Extract parameters
            method['parameters'] = self.extract_parameters(signature_lines)

            # Extract return type
            method['return_type'] = self.extract_return_type(method_content)

            # Extract description
            desc_match = re.search(self.patterns.METHOD_DESC, method_content, re.DOTALL)
            if desc_match:
                method['description'] = self.clean_description(desc_match.group(1).strip())

            methods.append(method)

        return methods

    def extract_parameters(self, signature: str) -> List[str]:
        """Extract parameters from method signature"""
        params = []
        param_match = re.search(r'\((.*?)\)', signature)
        if param_match:
            param_str = param_match.group(1)
            if param_str.strip():
                params = [p.strip() for p in param_str.split(',')]
        return params

    def extract_return_type(self, content: str) -> str:
        """Extract return type from method content"""
        return_match = re.search(r'Return.*?Type:\s*(\w+(?:\.\w+)*)', content, re.DOTALL)
        if return_match:
            return return_match.group(1)
        return ''