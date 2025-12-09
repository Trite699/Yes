import os
import glob
import subprocess
from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
CONVERTER_FOLDER = 'Converter'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

CONVERTERS = {
    "GMD": "gs56-gmd-converter.py",
    "Script": "gs56-script-converter.py",
    "Sounds PC": "asrc31.py",
    "Sounds NSW": "asrc31-nsw.py"
}

COMMAND_SETS = {
    "GMD": [
        ("i", "i (Import)"),
        ("d", "d (Decrypt)"),
        ("e", "e (Encrypt)")
    ],
    "Script": [
        ("i", "i (Import)"),
        ("d", "d (Decrypt)"),
        ("e", "e (Encrypt)")
    ],
    "Sounds PC": [
        ("e", "e (Encode)"),
        ("d", "d (Decode)"),
        ("i", "i (Info)"),
        ("r", "r (Replace)")
    ],
    "Sounds NSW": [
        ("e", "e (Encode)"),
        ("d", "d (Decode)"),
        ("i", "i (Info)"),
        ("r", "r (Replace)")
    ]
}


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        converter = request.form.get("converter")
        command = request.form.get("command")

        if 'file' not in request.files:
            return "No file uploaded"

        file = request.files['file']
        if file.filename == '':
            return "No file selected"

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        converter_script = os.path.join(CONVERTER_FOLDER, CONVERTERS[converter])

        # ------------------------------
        # BUILD CORRECT COMMAND (NO OUTPUT PATH)
        # ------------------------------
        cmd = ['python', converter_script, command]

        # GS5 encryption requires --xor
        if converter == "GMD" and command == "e" and filename.startswith("GS5"):
            cmd.append("--xor")

        cmd.append(input_path)

        # ------------------------------
        # RUN CONVERSION
        # ------------------------------
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Conversion failed:<br><pre>{result.stderr}</pre>"

        # ------------------------------
        # FIND OUTPUT FILE CREATED BY CONVERTER
        # ------------------------------
        output_file = detect_output_file(filename)

        if not output_file:
            return "Conversion complete, but no output file was found."

        return send_file(output_file, as_attachment=True)

    # ------------------------------
    # HTML UI
    # ------------------------------
    return render_template_string('''
    <!doctype html>
    <title>Upload & Convert</title>
    <h1>Upload File for Conversion</h1>

    <form method="post" enctype="multipart/form-data">
      <label>Choose converter:</label>
      <select name="converter" id="converter" onchange="updateCommands()">
        <option value="GMD">GMD</option>
        <option value="Script">Script</option>
        <option value="Sounds PC">Sounds PC</option>
        <option value="Sounds NSW">Sounds NSW</option>
      </select><br><br>

      <label>Choose command:</label>
      <select name="command" id="command"></select><br><br>

      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>

    <script>
      const COMMANDS = {
        "GMD": [["i","i (Import)"],["d","d (Decrypt)"],["e","e (Encrypt)"]],
        "Script": [["i","i (Import)"],["d","d (Decrypt)"],["e","e (Encrypt)"]],
        "Sounds PC": [["e","e (Encode)"],["d","d (Decode)"],["i","i (Info)"],["r","r (Replace)"]],
        "Sounds NSW": [["e","e (Encode)"],["d","d (Decode)"],["i","i (Info)"],["r","r (Replace)"]]
      };

      function updateCommands() {
        let converter = document.getElementById("converter").value;
        let select = document.getElementById("command");

        select.innerHTML = "";
        COMMANDS[converter].forEach(c => {
          let opt = document.createElement("option");
          opt.value = c[0];
          opt.textContent = c[1];
          select.appendChild(opt);
        });
      }
      window.onload = updateCommands;
    </script>
    ''')


def detect_output_file(filename):
    """Detect output file produced by the converter."""

    base = os.path.splitext(filename)[0]

    # Possible output extensions for GMD/script
    possible_exts = ["*.gmd", "*.txt", "*.json"]

    found_files = []
    for ext in possible_exts:
        found_files += glob.glob(os.path.join(CONVERTER_FOLDER, base + ext))

    if found_files:
        return found_files[0]

    # Sound converters output .wav or .bin
    sound_exts = ["*.wav", "*.bin"]
    for ext in sound_exts:
        found_files += glob.glob(os.path.join(CONVERTER_FOLDER, base + ext))

    return found_files[0] if found_files else None


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
