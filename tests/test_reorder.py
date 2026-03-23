
import sys
import os
from pathlib import Path
from pypdf import PdfWriter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from get_hands_on.core.pdf_ops import reorder_pages

def create_dummy_pdf(filename, pages=5):
    writer = PdfWriter()
    for i in range(pages):
        writer.add_blank_page(width=100, height=100)
    with open(filename, 'wb') as f:
        writer.write(f)
    print(f"Created dummy PDF: {filename} with {pages} pages")

def test_reorder():
    input_pdf = Path("test_input.pdf")
    output_pdf = Path("test_reordered.pdf")
    
    create_dummy_pdf(input_pdf, 5)
    
    # New order: [5, 1, 2, 3, 4] (Rotate right visually)
    new_order = [5, 1, 2, 3, 4]
    
    print(f"Reordering to: {new_order}")
    try:
        result = reorder_pages(input_pdf, output_pdf, new_order, log_cb=print)
        print(f"Success! Result: {result}")
        
        # Verify
        from pypdf import PdfReader
        reader = PdfReader(str(output_pdf))
        if len(reader.pages) == 5:
            print("Verified page count: 5")
        else:
            print(f"FAILED: Page count is {len(reader.pages)}")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    if input_pdf.exists(): os.remove(input_pdf)
    if output_pdf.exists(): os.remove(output_pdf)

if __name__ == "__main__":
    test_reorder()
