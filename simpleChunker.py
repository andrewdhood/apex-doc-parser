import json
import re
import pdfplumber

def extract_data(file_path):
    """
    Extracts data from a PDF file (specifically the Apex Reference Guide) and structures it into a JSON format
    using the pdfplumber library.

    This function reads the content of the PDF file page by page, splits each page into sections based on
    page markers, and then extracts the title and content of each section. It handles cases where there
    might not be a clear separation between title and content. It also identifies list items, code blocks,
    and method signatures, including their parameters and return types.

    The extracted data is then organized into a JSON structure with the document name and a list of sections,
    each containing a title and a list of content items (paragraphs, lists, or code blocks).

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        dict: A dictionary containing the structured data in JSON format.
    """

    data = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # Extract text content from the page
            text = page.extract_text()

            # Split the content into sections based on page markers (assuming each page is a section)
            sections = re.split(r'--- PAGE \d+ ---\n', text)[1:]  # Skip the first empty split

            for section in sections:
                # Split each section into title and content, but handle cases with no empty line
                try:
                    title, content = re.split(r'\n\n', section, 1)
                except ValueError:
                    # If no empty line, assume the whole section is the content
                    title = ""  # Or you can set a default title
                    content = section

                # Remove page numbers and extra whitespaces from the title
                title = re.sub(r'\d+', '', title).strip()

                # Remove leading and trailing whitespaces from the content
                content = content.strip()

                # Split the content into paragraphs based on a capital letter at the beginning of a line
                paragraphs = re.split(r'\n(?=[A-Z])', content)

                content_list = []
                for paragraph in paragraphs:
                    # Check if the paragraph is a list (starts with '*')
                    if paragraph.startswith('*'):
                        list_items = paragraph.strip().split('\n')
                        content_list.append({
                            "type": "list",
                            "content": [item.strip()[2:] for item in list_items]
                        })
                    # Check if the paragraph is a code block (starts with 'Signature')
                    elif paragraph.startswith('Signature'):
                        content_list.append({
                            "type": "code",
                            "content": paragraph.strip()
                        })
                    # Check if the paragraph is a method signature (contains 'public' or 'global')
                    elif 'public ' in paragraph or 'global ' in paragraph or 'static ' in paragraph:
                        # Extract method signature details (name, parameters, return type)
                        match = re.match(r'(public|global|static)\s+([\w<>\[\]\s]+)\s+(\w+)\s*\((.*)\)', paragraph)
                        if match:
                            return_type = match.group(2).strip()
                            name = match.group(3)
                            parameters_str = match.group(4)
                            parameters = []
                            if parameters_str:
                                # Split parameters by comma, but handle commas within nested types
                                for param in re.split(r',\s*(?![^<>\[\]()]*[\])])', parameters_str):
                                    param_parts = param.strip().split(' ')
                                    parameters.append({
                                        "type": ' '.join(param_parts[:-1]),  # Handle multi-word types
                                        "name": param_parts[-1]
                                    })
                            content_list.append({
                                "type": "method",
                                "name": name,
                                "signature": paragraph.strip(),
                                "parameters": parameters,
                                "return_type": return_type
                            })
                        else:
                            # If not a method signature, treat it as a regular paragraph
                            content_list.append({
                                "type": "paragraph",
                                "content": paragraph.strip()
                            })
                    else:
                        # If not a list or code block, treat it as a regular paragraph
                        content_list.append({
                            "type": "paragraph",
                            "content": paragraph.strip()
                        })

                data.append({
                    "title": title,
                    "content": content_list
                })

    json_data = {
        "document": "Apex Reference Guide",
        "sections": data
    }

    return json_data

# Example usage:
file_path = 'apex_reference.pdf'  # Replace with your PDF file path
json_data = extract_data(file_path)

# Save the extracted data to a JSON file
with open('output.json', 'w') as f:
    json.dump(json_data, f, indent=4)