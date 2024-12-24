# run.py
from pathlib import Path
from processor import PDFDocProcessor

def main():
    # Get the current directory
    current_dir = Path.cwd()
    
    # Define input and output paths
    pdf_path = current_dir / "apex_reference.pdf"
    output_path = current_dir / "apex_reference.json"
    
    # Initialize processor
    processor = PDFDocProcessor(debug=True)
    
    # Process PDF
    print(f"Processing PDF: {pdf_path}")
    data = processor.process_pdf(str(pdf_path))
    
    if data:
        # Save results
        processor.save_json(data, str(output_path))
        print(f"JSON saved to: {output_path}")
    else:
        print("No data was processed")

if __name__ == "__main__":
    main()