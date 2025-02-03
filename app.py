from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import json
from google.cloud import storage
from google.oauth2 import service_account

app = Flask(__name__)

# Use the file path from the environment variable
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not credentials_path:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

# Authenticate using the service account key file
client = storage.Client.from_service_account_json(credentials_path)
bucket = client.bucket('svi-preservation-data')

# Route to serve the main index.html
@app.route('/')
def index():
    return render_template('index.html')

# Serve files.json for metadata
@app.route('/files.json')
def get_files_json():
    return send_from_directory('.', 'files.json')

# API to filter files based on query parameters
@app.route('/filter', methods=['GET'])
def filter_files():
    with open('files.json') as f:
        files_data = json.load(f)

    year = request.args.get('year', '')
    location = request.args.get('location', '')
    geography = request.args.get('geography', '')
    file_type = request.args.get('file_type', '')

    filtered_files = [
        file for file in files_data
        if (year.lower() in file.get('year', '').lower() if year else True) and
           (location.lower() in file.get('location', '').lower() if location else True) and
           (geography.lower() in file.get('geography', '').lower() if geography else True) and
           (file_type.lower() in file.get('type', '').lower() if file_type else True)
    ]

    return jsonify(filtered_files)

# Download file handler
@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    with open('files.json') as f:
        files_data = json.load(f)

    file_info = next((file for file in files_data if file['fileName'] == filename), None)

    if file_info:
        gcs_path = file_info.get('localPath')
        if not gcs_path:
            return jsonify({"error": "Invalid file path."}), 404

        # Generate signed URL with proper headers
        blob = bucket.blob(gcs_path)
        signed_url = blob.generate_signed_url(
            version='v4',
            expiration=3600,  # 1-hour expiry
            response_disposition=f'attachment; filename="{file_info["fileName"]}"',
            response_type='text/csv' if filename.endswith('.csv') else 'application/zip'
        )

        return jsonify({"downloadUrl": signed_url})

    return jsonify({"error": "File not found."}), 404



# Custom error handler for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return "404 - File Not Found", 404

if __name__ == '__main__':
    # Use the port provided by Render, default to 4000 if not set
    port = int(os.environ.get("PORT", 4000))

    # Bind to 0.0.0.0 so Render can detect the open port
    app.run(host='0.0.0.0', port=port, debug=True)
