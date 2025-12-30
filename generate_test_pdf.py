import fitz  # PyMuPDF

def create_watermarked_pdf(filename="test_watermarked.pdf", pages=5):
    doc = fitz.open()
    
    for i in range(pages):
        page = doc.new_page()
        
        # Add some regular content
        page.insert_text((50, 50), f"This is page {i+1} content.", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 70), "This is some important information that should remain.", fontsize=12, color=(0, 0, 0))
        
        # Add a text watermark (diagonal)
        # Using a distinct color (light gray) and large font
        page.insert_text(
            (100, 300), 
            "CONFIDENTIAL WATERMARK", 
            fontsize=50, 
            color=(0.8, 0.8, 0.8)
        )
        
        # Add another small repeating watermark at the bottom
        page.insert_text(
            (200, 800), 
            "Draft Copy", 
            fontsize=10, 
            color=(1, 0, 0) # Red watermark
        )

    doc.save(filename)
    print(f"Created {filename} with {pages} pages.")

if __name__ == "__main__":
    create_watermarked_pdf()
