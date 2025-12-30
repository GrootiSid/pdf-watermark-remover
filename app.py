import os
import io
import base64
from flask import Flask, render_template, request, jsonify
from watermark_remover import analyze_pdf_for_watermarks, remove_watermarks
import fitz

app = Flask(__name__)

# Serverless: No permanent file system access. We use in-memory processing.

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    sensitivity = float(request.form.get('sensitivity', 0.8))

    try:
        # 1. Read file into memory
        input_stream = file.read()
        
        # 2. Analyze (Need to adapt logic to accept streams or temporary files)
        # Since analyze_pdf_for_watermarks expects a path, we'll adapt strictly here
        # OR better, we refactor watermark_remover.py. 
        # For minimal friction, let's write to /tmp (Vercel allows /tmp) for analysis
        # BUT standard approach: Refactor helper to accept document object.
        
        # Opening doc from stream
        doc = fitz.open(stream=input_stream, filetype="pdf")
        
        # --- LOGIC MOVED INLINE TO SUPPORT DOC OBJECT ---
        # Analyze
        candidates = {}
        # Simple Counter replacement logic for inline
        # ... actually, let's just write to /tmp for SAFETY and reuse existing logic 
        # without rewriting the complex helper right now. 
        # Vercel supports /tmp.
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(input_stream)
            tmp_input_path = tmp_input.name
            
        try:
            # Analyze
            watermarks = analyze_pdf_for_watermarks(tmp_input_path, threshold_ratio=sensitivity)
            
            if not watermarks:
                 return jsonify({
                    'message': 'No consistent watermarks detected.',
                    'status': 'no_watermarks'
                })
            
            # Remove
            output_path = tmp_input_path + "_clean.pdf"
            remove_watermarks(tmp_input_path, output_path, watermarks)
            
            # Read back processed file
            with open(output_path, "rb") as f:
                processed_data = f.read()
                
            # Clean up
            if os.path.exists(output_path): os.remove(output_path)
            
        finally:
            if os.path.exists(tmp_input_path): os.remove(tmp_input_path)

        # 3. Return Base64
        b64_data = base64.b64encode(processed_data).decode('utf-8')
        
        return jsonify({
            'message': 'Watermarks removed successfully!',
            'status': 'success',
            'file_base64': b64_data,
            'filename': f"clean_{file.filename}",
            'removed_count': len(watermarks)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
