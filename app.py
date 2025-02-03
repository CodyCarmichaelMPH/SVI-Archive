from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import json

app = Flask(__name__)

# Route to serve the main index.html
@app.route('/')
def index():
    return render_template('index.html')

# Serve files.json for metadata
@app.route('/files.json')
def get_files_json():
    return send_from_directory('.', 'files.json')

# Serve CSV and ESRI Data
@app.route('/data/<path:filename>')
def download_data(filename):
    directory = os.path.dirname(filename)
    return send_from_directory(directory or '.', os.path.basename(filename), as_attachment=True)

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

# Custom error handler for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return "404 - File Not Found", 404

if __name__ == '__main__':
    app.run(debug=True)
