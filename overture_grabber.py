from flask import Flask, request, Response, render_template, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/download_geojson', methods=['POST'])
def download_geojson():
    bbox = request.json.get('bbox')
    feature_type = request.json.get('type', 'place')
    limit = request.json.get('limit', 1000)  # Default limit of 1000 features
    
    if not bbox or len(bbox) != 4 or not feature_type:
        return {"error": "Invalid input"}, 400

    # Prepare the command with size limits
    command = [
        'overturemaps', 'download',
        '--bbox', ','.join(map(str, bbox)),
        '-f', 'geojson',
        '--type', feature_type,
        '--limit', str(limit)
    ]

    # Stream the output with explicit buffer clearing
    def generate():
        try:
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=4096  # Set a reasonable buffer size
            )
            
            for line in iter(process.stdout.readline, ''):
                yield line
                
            process.stdout.close()
            return_code = process.wait(timeout=30)  # Add timeout
            if return_code:
                raise subprocess.CalledProcessError(return_code, command)
                
        except Exception as e:
            app.logger.error(f"Error in download_geojson: {str(e)}")
            raise
        finally:
            if process:
                try:
                    process.kill()  # Ensure process is terminated
                except:
                    pass

    return Response(
        generate(),
        mimetype="application/geo+json",
        headers={
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Cache-Control': 'no-cache'  # Prevent caching
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)