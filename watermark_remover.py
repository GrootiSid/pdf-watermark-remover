import fitz
import argparse
from collections import Counter

def analyze_pdf_for_watermarks(input_path: str, sample_pages=10, threshold_ratio=0.8):
    """
    Analyzes the PDF to find potential watermarks.
    Returns a list of 'signatures' (text content, bounding box approximate) that appear on > threshold_ratio of the sampled pages.
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)
    
    # Determine pages to sample
    if total_pages <= sample_pages:
        pages_to_check = range(total_pages)
    else:
        # Sample spread: start, middle, end
        start_pages = range(0, min(total_pages, sample_pages // 3))
        end_pages = range(max(0, total_pages - sample_pages // 3), total_pages)
        mid_start = total_pages // 2 - (sample_pages // 3) // 2
        mid_pages = range(mid_start, mid_start + sample_pages // 3)
        
        pages_to_check = set(list(start_pages) + list(mid_pages) + list(end_pages))
        pages_to_check = [p for p in pages_to_check if 0 <= p < total_pages]

    print(f"Analyzing {len(pages_to_check)} pages out of {total_pages} to detect watermarks...")

    # Dictionary to track text occurrences: key=(text_content, rounded_rect_tuple, color_tuple), value=count
    # Note: We round rect coordinates to group slightly shifted items
    candidates = Counter()
    
    for page_num in pages_to_check:
        page = doc[page_num]
        
        # Analyze Text
        text_instances = page.get_text("dict")["blocks"]
        for block in text_instances:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        
                        bbox = fitz.Rect(span["bbox"])
                        # Round bbox to nearest integer to handle slight variations
                        rounded_bbox = (round(bbox.x0), round(bbox.y0), round(bbox.x1), round(bbox.y1))
                        
                        # We also track color/size to ensure we don't accidentally match headers/footers unless they are pervasive
                        color = span["color"]
                        size = round(span["size"], 1)
                        
                        key = ("text", text, rounded_bbox, color, size)
                        candidates[key] += 1

        # Analyze Drawings/Images (Simplified for now to just text watermarks as requested, but structure is here)
        # Implementing drawing removal is harder without visual analysis, effectively we stick to text for now
        # or simple drawings if they are identical.

    # Filter candidates
    threshold_count = len(pages_to_check) * threshold_ratio
    watermarks = []
    
    print("\n--- Potential Watermarks Detected ---")
    for key, count in candidates.items():
        if count >= threshold_count:
            type_, content, bbox_tuple, color, size = key
            print(f"Type: {type_}, Text: '{content}', Loc: {bbox_tuple}, Count: {count}/{len(pages_to_check)}")
            watermarks.append({
                "type": type_,
                "content": content,
                "bbox": fitz.Rect(bbox_tuple),
                "color": color,
                "size": size
            })

    doc.close()
    return watermarks

def remove_watermarks(input_path: str, output_path: str, watermarks: list):
    """
    Removes the identified watermarks from the PDF.
    """
    doc = fitz.open(input_path)
    
    removed_count = 0
    
    for page in doc:
        # We need to clean text. PyMuPDF doesn't support "deleting" text objects easily from the stream 
        # without redaction annotations which essentially draw over it.
        # However, redactions are the standard way to "remove" content.
        
        for wm in watermarks:
            if wm["type"] == "text":
                # Search for this text on the page
                # We use a slightly looser search to ensure we catch it
                hits = page.search_for(wm["content"])
                
                for rect in hits:
                    # check if this rect roughly matches the watermark rect (to avoid deleting same text in valid running text)
                    if intersect_percent(rect, wm["bbox"]) > 0.5:
                        page.add_redact_annot(rect, fill=(1, 1, 1)) # masking with white, modify if transparent needed
                        # Ideally we want to remove proper, but 'clean' is hard.
                        # Actually, let's try to just use 'apply_redactions' which deletes the content.
                        removed_count += 1
        
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE) # Don't touch images unless specified

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f"\nSaved cleaned PDF to: {output_path}")
    print(f"Removed approx {removed_count} instances.")

def intersect_percent(rect1, rect2):
    # Returns how much of rect1 is covered by rect2
    # Logic: if the watermark location is remarkably consistent, the intersection should be high.
    
    # Check for simple inclusion or near match
    # Expand rect2 slightly to be safe
    expanded = fitz.Rect(rect2)
    expanded.x0 -= 2
    expanded.y0 -= 2
    expanded.x1 += 2
    expanded.y1 += 2
    
    if expanded.contains(rect1):
        return 1.0
        
    intersect = rect1 & rect2
    if intersect.is_empty:
        return 0.0
    
    return intersect.get_area() / rect1.get_area()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF Watermark Remover")
    parser.add_argument("input_pdf", help="Path to input PDF")
    parser.add_argument("--output", default="cleaned_output.pdf", help="Path to output PDF")
    parser.add_argument("--sensitivity", type=float, default=0.8, help="Frequency threshold (0-1) for detection")
    
    args = parser.parse_args()
    
    found_watermarks = analyze_pdf_for_watermarks(args.input_pdf, threshold_ratio=args.sensitivity)
    
    if not found_watermarks:
        print("No consistent watermarks detected.")
    else:
        remove_watermarks(args.input_pdf, args.output, found_watermarks)
