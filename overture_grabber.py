from flask import Flask, request, Response, render_template, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/download_geojson', methods=['POST'])
def download_geojson():
    bbox = request.json.get('bbox')
    feature_type = request.json.get('type', 'place')  # Default to 'place' if type not specified
    
    if not bbox or len(bbox) != 4 or not feature_type:
        return {"error": "Invalid input"}, 400

    # Prepare the command to write output to stdout
    command = [
        'overturemaps', 'download',
        '--bbox', ','.join(map(str, bbox)),
        '-f', 'geojson',
        '--type', feature_type,
    ]

    # Stream the output of the command directly as a response
    def generate():
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in iter(process.stdout.readline, ''):
            yield line
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

    return Response(generate(), mimetype="application/geo+json")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)