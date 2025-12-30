import os
import uuid
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from watermark_remover import analyze_pdf_for_watermarks, remove_watermarks

app = Flask(__name__)

# Configure upload/download folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

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

    if file:
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_filename = f"{unique_id}_{filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        file.save(input_path)

        # Get sensitivity from request or default
        sensitivity = float(request.form.get('sensitivity', 0.8))

        try:
            # 1. Analyze
            watermarks = analyze_pdf_for_watermarks(input_path, threshold_ratio=sensitivity)
            
            if not watermarks:
                return jsonify({
                    'message': 'No consistent watermarks detected.',
                    'status': 'no_watermarks'
                })

            # 2. Remove (Auto-processing for now)
            output_filename = f"clean_{input_filename}"
            output_path = os.path.join(app.config['DOWNLOAD_FOLDER'], output_filename)
            
            remove_watermarks(input_path, output_path, watermarks)
            
            return jsonify({
                'message': 'Watermarks removed successfully!',
                'status': 'success',
                'download_url': f'/download/{output_filename}',
                'removed_count': len(watermarks) # Approximation
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['DOWNLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
