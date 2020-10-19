import imghdr
import os
from flask import Flask, render_template, request, redirect, url_for, abort, \
    send_from_directory
from werkzeug.utils import secure_filename
import video
import subprocess
import uuid

conversion_jobs = {}
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.mp4', '.mkv', '.ogv']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['DOWNLOAD_PATH'] = 'downloads'

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

def clear_files():
    print("+++Clearing uploads...")
    files = os.listdir(app.config['UPLOAD_PATH'])
    for file_name in files:
        current_file = os.path.join(app.config['UPLOAD_PATH'],file_name)
        os.remove(current_file)
        print(f"Erasing {current_file}")

    print("+++Clearing downloads...")
    files = os.listdir(app.config['DOWNLOAD_PATH'])
    for file_name in files:
        current_file = os.path.join(app.config['DOWNLOAD_PATH'],file_name)
        os.remove(current_file)
        print(f"Erasing {current_file}")

@app.errorhandler(413)
def too_large(e):
    return "Video is too large", 413

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    export_types = []

    for i in range(1,10,1):
        current_type = f"{request.form.get('type'+str(i), 'false')}"
        if current_type != 'false':
            export_types.append(current_type)

    if len(export_types) == 0:
        export_types.append("Fast 480p30")

    separator = ","
    profiles = f"{separator.join(export_types)}"

    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']: #or file_ext != validate_image(uploaded_file.stream):
            return "Invalid video file", 400
        savePath = os.path.join(app.config['UPLOAD_PATH'], filename)
        uploaded_file.save(savePath)

    job_id = str(uuid.uuid4())
    p = subprocess.Popen(f"python video.py {savePath} --presets '{profiles}' --job {job_id}", shell=True)
    print(f"returning job_id: {job_id}")
    return job_id

@app.route('/downloads/<filename>')
def upload(filename):
    return send_from_directory(app.config['DOWNLOAD_PATH'], filename)

@app.route('/status/get/<job>')
def getstatus(job: str):
    response = "Job not created yet"
    if job in conversion_jobs:
        response = conversion_jobs[job]

    return str(response), 200

@app.route('/status/set/<job>/<value>')
def setstatus(job: str, value: str):
    conversion_jobs[job] = value 
    return "OK", 200

app.before_first_request(clear_files)