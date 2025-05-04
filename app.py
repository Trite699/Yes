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

# Specify which converters need a command argument
COMMAND_NEEDED = {"GMD", "Script"}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        converter = request.form.get("converter")
        command = request.form.get("command")  # May be None
        if 'file' not in request.files or not converter:
            return "No file or converter selected"
        if converter in COMMAND_NEEDED and not command:
            return "No command selected for this converter"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f'converted_{filename}')
        file.save(input_path)

        # Build the subprocess command
        converter_script = os.path.join("Converter", CONVERTERS[converter])
        if converter in COMMAND_NEEDED:
            cmd = ['python', converter_script, command, input_path, output_path]
        else:
            cmd = ['python', converter_script, input_path, output_path]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Conversion failed:<br><pre>{result.stderr}</pre>"

        return send_file(output_path, as_attachment=True)

    # HTML form lets user pick converter and command
    return render_template_string('''
    <!doctype html>
    <title>Upload and Convert</title>
    <h1>Upload File for Conversion</h1>
    <form method=post enctype=multipart/form-data>
      <label for="converter">Choose converter:</label>
      <select name="converter" id="converter" onchange="toggleCommandDropdown()">
        <option value="GMD">GMD</option>
        <option value="Script">Script</option>
        <option value="Sounds PC">Sounds PC</option>
        <option value="Sounds NSW">Sounds NSW</option>
      </select><br><br>
      <div id="commandDiv">
        <label for="command">Choose command:</label>
        <select name="command" id="command">
          <option value="i">i (Import)</option>
          <option value="d">d (Decrypt)</option>
          <option value="e">e (Encrypt)</option>
        </select><br><br>
      </div>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    <script>
      function toggleCommandDropdown() {
        var converter = document.getElementById('converter').value;
        var commandDiv = document.getElementById('commandDiv');
        if (converter === 'GMD' || converter === 'Script') {
          commandDiv.style.display = 'block';
        } else {
          commandDiv.style.display = 'none';
        }
      }
      window.onload = toggleCommandDropdown;
    </script>
    ''')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
