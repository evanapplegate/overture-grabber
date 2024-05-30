from flask import Flask, request, send_file, render_template, jsonify
import subprocess
import os
import tempfile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/download_geojson', methods=['POST'])
def download_geojson():
    bbox = request.json.get('bbox')
    feature_type = request.json.get('type', 'place')  # Use the type from the request, default to 'place'
    
    if not bbox or len(bbox) != 4 or not feature_type:
        return {"error": "Invalid input"}, 400
    
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.geojson').name
    command = [
        'overturemaps', 'download',
        '--bbox', ','.join(map(str, bbox)),
        '-f', 'geojson',
        '--type', feature_type,
        '-o', output_file
    ]
    
    try:
        subprocess.run(command, check=True)
        return send_file(output_file, as_attachment=True, download_name=f'{feature_type}.geojson')
    except subprocess.CalledProcessError:
        os.unlink(output_file)  # Clean up temporary file
        return {"error": "Failed to download geojson"}, 500

if __name__ == '__main__':
    app.run(debug=True)