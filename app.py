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

def calculate_delay(file_path, base_delay=3, additional_delay_per_mb=1):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to megabytes
    total_delay = base_delay + (file_size_mb * additional_delay_per_mb)
    return total_delay

@app.route('/generate_views')
def generate_views():
    prusa_slicer_path = '/home/egr/gcodereview/PrusaSlicer-2.7.0+linux-x64-GTK3-202311231454.AppImage'  # Update with your path

    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith(('.gcode', '.gco', '.g')):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Launch PrusaSlicer with the G-code file
            subprocess.Popen([prusa_slicer_path, file_path])
            delay = calculate_delay(file_path)
            print('Sleep for ' + str(delay) + 'seconds...\n ')
            time.sleep(delay)
            print('Sleep done, press \'l\' and take a screenshot.\n')
            # Take a screenshot
            # Get the screen size
            screenWidth, screenHeight = pyautogui.size()
            # Calculate the center of the screen
            centerX, centerY = screenWidth / 1.2, screenHeight / 2
            # Move the mouse to the center and click
            pyautogui.click(centerX, centerY)
            time.sleep(2)
            pyautogui.press('l')
            time.sleep(2)
            regionWidth = int(screenWidth * 2 / 3)
            regionHeight = int(screenHeight * 2 / 3)
            startX = int((screenWidth - regionWidth) / 2)
            startY = int((screenHeight - regionHeight) / 2)

            # Take a screenshot of the specified region
            screenshot = pyautogui.screenshot(region=(startX, startY, regionWidth, regionHeight))
            #screenshot = pyautogui.screenshot()
            screenshot.save(os.path.splitext(file_path)[0] + '-image1.jpg')
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'q')
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
    #image_source_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image_source_path = image_filename
    image_dest_path = os.path.join('static', image_filename)
    image_exists = False

    print('Check if ' + image_filename + ' exists\n')
    if os.path.exists(image_filename):
        print('Image does exist. Copy it from ' + image_source_path + ' to' + image_dest_path + '\n')
        shutil.copy(image_source_path, image_dest_path)
        image_exists = True

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
    app.run(host='0.0.0.0', debug=True)
