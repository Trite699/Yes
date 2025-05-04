import os
import subprocess
from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)

CONVERTERS = {
    "GMD": "gs56-gmd-converter.py",
    "Script": "gs56-script-converter.py",
    "Sounds PC": "asrc31.py",
    "Sounds NSW": "asrc31-nsw.py"
}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        converter = request.form.get("converter")
        if 'file' not in request.files or not converter:
            return "No file or converter selected"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f'converted_{filename}')
        file.save(input_path)

        # Run the converter script
        converter_script = os.path.join("Converter", CONVERTERS[converter])
        result = subprocess.run(
            ['python', converter_script, input_path, output_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Conversion failed:<br><pre>{result.stderr}</pre>"

        return send_file(output_path, as_attachment=True)

    # HTML form lets user pick converter
    return render_template_string('''
    <!doctype html>
    <title>Upload and Convert</title>
    <h1>Upload File for Conversion</h1>
    <form method=post enctype=multipart/form-data>
      <label for="converter">Choose converter:</label>
      <select name="converter" id="converter">
        <option value="GMD">GMD</option>
        <option value="Script">Script</option>
        <option value="Sounds PC">Sounds PC</option>
        <option value="Sounds NSW">Sounds NSW</option>
      </select><br><br>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    ''')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
