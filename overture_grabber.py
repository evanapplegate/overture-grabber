from flask import Flask, request, Response, render_template, jsonify
import subprocess
import os
import sys
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/download_geojson', methods=['POST'])
def download_geojson():
    request_id = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    logging.info(f"[{request_id}] New download request received")
    
    bbox = request.json.get('bbox')
    feature_type = request.json.get('type', 'place')
    
    logging.info(f"[{request_id}] Parameters: feature_type={feature_type}, bbox={bbox}")
    
    if not bbox or len(bbox) != 4 or not feature_type:
        logging.error(f"[{request_id}] Invalid input parameters")
        return {"error": "Invalid input"}, 400

    command = [
        'overturemaps', 'download',
        '--bbox', ','.join(map(str, bbox)),
        '-f', 'geojson',
        '--type', feature_type
    ]
    
    logging.info(f"[{request_id}] Executing command: {' '.join(command)}")

    def generate():
        process = None
        bytes_sent = 0
        start_time = datetime.now()
        current_chunk = ""
        
        try:
            logging.info(f"[{request_id}] Starting subprocess")
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=4096
            )
            
            # Handle stderr in a non-blocking way
            def log_stderr():
                for line in iter(process.stderr.readline, ''):
                    logging.error(f"[{request_id}] CLI Error: {line.strip()}")
            
            import threading
            stderr_thread = threading.Thread(target=log_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()
            
            logging.info(f"[{request_id}] Starting to stream response")
            
            # Increased timeout for larger datasets
            timeout = 120  # 2 minutes
            has_data = False
            feature_count = 0
            
            # Send the opening of the GeoJSON
            yield '{"type":"FeatureCollection","features":['
            first_feature = True
            
            for line in iter(process.stdout.readline, ''):
                current_time = datetime.now()
                if (current_time - start_time).total_seconds() > timeout:
                    logging.error(f"[{request_id}] Command timed out after {timeout} seconds")
                    process.kill()
                    # Close the GeoJSON properly even on timeout
                    yield ']}'
                    raise TimeoutError(f"Command timed out after {timeout} seconds")
                
                has_data = True
                bytes_sent += len(line)
                
                # Accumulate the line into current_chunk
                current_chunk += line
                
                # Check if we have a complete feature (contains both { and })
                if '{' in current_chunk and '}' in current_chunk:
                    try:
                        # Add comma between features, except for the first one
                        if not first_feature:
                            yield ','
                        else:
                            first_feature = False
                            
                        yield current_chunk.strip()
                        feature_count += 1
                        current_chunk = ""
                        
                        if bytes_sent % 1000000 == 0:  # Log every ~1MB
                            logging.info(f"[{request_id}] Streamed {bytes_sent/1000000:.1f}MB, {feature_count} features")
                            # Send progress info as a comment in the GeoJSON
                            progress_msg = f',{{"__progress":true,"mb":{bytes_sent/1000000:.1f},"features":{feature_count}}}'
                            yield progress_msg
                            
                    except Exception as e:
                        logging.error(f"[{request_id}] Error processing feature: {str(e)}")
                        continue
            
            # Close the GeoJSON
            yield ']}'
            
            if not has_data:
                logging.error(f"[{request_id}] No data received from command")
                raise Exception("No data received from command")
            
            process.stdout.close()
            logging.info(f"[{request_id}] Waiting for process to complete")
            return_code = process.wait(timeout=5)  # Short timeout for process cleanup
            
            if return_code:
                error_msg = f"Process failed with return code {return_code}"
                logging.error(f"[{request_id}] {error_msg}")
                raise subprocess.CalledProcessError(return_code, command)
            
            logging.info(f"[{request_id}] Download completed successfully. Total bytes: {bytes_sent}, features: {feature_count}")
                
        except Exception as e:
            logging.error(f"[{request_id}] Error in download_geojson: {str(e)}", exc_info=True)
            # Return a JSON error response that the client can handle
            yield '{"error": "' + str(e).replace('"', '\\"') + '"}\n'
        finally:
            if process:
                try:
                    process.kill()
                    logging.info(f"[{request_id}] Process cleaned up")
                except Exception as kill_error:
                    logging.error(f"[{request_id}] Error killing process: {kill_error}")

    logging.info(f"[{request_id}] Setting up response stream")
    return Response(
        generate(),
        mimetype="application/json",
        headers={
            'X-Accel-Buffering': 'no',
            'Cache-Control': 'no-cache',
            'Connection': 'close',
            'X-Request-ID': request_id
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)