from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import shutil
import glob

#risky additions here for generate_views
import pyautogui
from PIL import ImageGrab
import subprocess
import time


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'sample-gcode'

@app.route('/')
def index():
    gcode_files = os.listdir(app.config['UPLOAD_FOLDER'])
    files_info = []
    for file in gcode_files:
        if file.lower().endswith(('.gcode', '.gco', '.g')):
            base_name = os.path.splitext(file)[0]
            processed_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}-image*.jpg"))
            is_processed = len(processed_files) > 0
            files_info.append({'name': file, 'processed': is_processed})
    return render_template('index.html', files_info=files_info)

def calculate_delay(file_path, base_delay=10, additional_delay_per_mb=1):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to megabytes
    total_delay = base_delay + (file_size_mb * additional_delay_per_mb)
    return total_delay

#risky addition here


@app.route('/generate_views')
def generate_views():
    prusa_slicer_path = '/home/egr/gcodereview/PrusaSlicer-2.7.0+linux-x64-GTK3-202311231454.AppImage'  # Update with your path

    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith(('.gcode', '.gco', '.g')):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Launch PrusaSlicer with the G-code file
            subprocess.Popen([prusa_slicer_path, file_path])
            delay = calculate_delay(file_path)
            time.sleep(delay)

            # Take a screenshot
            pyautogui.hotkey('l')
            time.sleep(2)
            screenshot = pyautogui.screenshot()
            screenshot.save(os.path.splitext(file_path)[0] + '-image1.jpg')

            # Close PrusaSlicer
            # pyautogui.hotkey('alt', 'f4')
            subprocess.Popen(['pkill', 'PrusaSlicer'])
            time.sleep(2)  # Give it a moment to close

    return redirect(url_for('index'))

@app.route('/file/<filename>')
def file_info(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_stats = os.stat(file_path)
    file_details = {
        'name': filename,
        'size': file_stats.st_size,
        'modified_date': datetime.fromtimestamp(file_stats.st_mtime)
    }
    image_filename = os.path.splitext(file_path)[0] + '-image1.jpg'
    image_exists = os.path.exists(image_filename)

    return render_template('file_info.html', file=file_details, image_filename=image_filename, image_exists=image_exists)
    #return render_template('file_info.html', file=file_details)

@app.route('/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file_to_folder():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
    return redirect(url_for('upload_file'))

@app.route('/accept/<filename>')
def accept_gcode(filename):
    source = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    destination = os.path.join(app.config['UPLOAD_FOLDER'], 'accepted-gcode', filename)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.move(source, destination)
    return redirect(url_for('index'))

@app.route('/reject/<filename>')
def reject_gcode(filename):
    source = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    destination = os.path.join(app.config['UPLOAD_FOLDER'], 'rejected-gcode', filename)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.move(source, destination)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='192.168.0.51', debug=True)
