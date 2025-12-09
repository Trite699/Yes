import os
import subprocess
from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)

CONVERTERS = {
    "GMD": "gs56-gmd-converter.py",
    "Script": "gs56-script-converter.py",
    "Sounds PC": "asrc31.py",
    "Sounds NSW": "asrc31-nsw.py"
}

COMMAND_SETS = {
    "GMD": [
        ("d", "d (Decode)"),
        ("e", "e (Encode)"),
        ("ex", "e (Encode with XOR)"),
        ("i", "i (Raw Dump)")
    ],
    "Script": [
        ("d", "d (Decode)"),
        ("e", "e (Encode)"),
        ("i", "i (Raw Dump)")
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
    if request.method == "POST":
        converter = request.form.get("converter")
        command = request.form.get("command")

        file = request.files.get("file")
        if not file:
            return "No file uploaded."

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        converter_script = os.path.join("Converter", CONVERTERS[converter])

        # --------------------
        #  GMD CORRECT COMMANDS
        # --------------------
        if converter == "GMD":

            if command == "d":
                cmd = ["python", converter_script, "d", input_path]

            elif command == "e":
                cmd = ["python", converter_script, "e", input_path]

            elif command == "ex":  # XOR ENCRYPT
                cmd = ["python", converter_script, "e", "--xor", input_path]

            elif command == "i":  # RAW DUMP
                out_dir = os.path.join(OUTPUT_FOLDER, filename + "_raw")
                os.makedirs(out_dir, exist_ok=True)
                cmd = ["python", converter_script, "i", "--out", out_dir, input_path]

        # --------------------
        # Script converter uses same format as GMD
        # --------------------
        elif converter == "Script":
            if command in ("d", "e"):
                cmd = ["python", converter_script, command, input_path]
            elif command == "i":
                out_dir = os.path.join(OUTPUT_FOLDER, filename + "_raw")
                os.makedirs(out_dir, exist_ok=True)
                cmd = ["python", converter_script, "i", "--out", out_dir, input_path]

        # --------------------
        # Sounds PC + NSW
        # --------------------
        else:
            output_path = os.path.join(OUTPUT_FOLDER, f"converted_{filename}")
            cmd = ["python", converter_script, command, input_path, output_path]

        # RUN THE COMMAND
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return f"<pre>{result.stderr}</pre>"

        # GMD + Script produce multiple files → give ZIP
        if converter in ("GMD", "Script") and command == "i":
            return f"Raw dump completed.<br>Output folder: {out_dir}"

        # Sounds return a single output file
        output_file = os.path.join(OUTPUT_FOLDER, f"converted_{filename}")
        if os.path.exists(output_file):
            return send_file(output_file, as_attachment=True)

        # GMD encode/decode produces a new file in same folder
        # find it
        possible = filename.rsplit('.', 1)[0]
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(possible) and f != filename:
                return send_file(os.path.join(UPLOAD_FOLDER, f), as_attachment=True)

        return "Conversion complete, but output file not found."

    # ------------------------
    # HTML UI
    # ------------------------
    return render_template_string("""
    <!doctype html>
    <title>Upload & Convert</title>
    <h1>Upload File</h1>

    <form method="post" enctype="multipart/form-data">
      <label>Converter:</label>
      <select name="converter" id="converter" onchange="updateCommands()">
        <option value="GMD">GMD</option>
        <option value="Script">Script</option>
        <option value="Sounds PC">Sounds PC</option>
        <option value="Sounds NSW">Sounds NSW</option>
      </select><br><br>

      <label>Command:</label>
      <select name="command" id="command"></select><br><br>

      <input type="file" name="file">
      <input type="submit" value="Convert">
    </form>

    <script>
      const COMMAND_SETS = {
        "GMD": [["d","d (Decode)"],["e","e (Encode)"],["ex","e (Encode XOR)"],["i","i (Raw Dump)"]],
        "Script": [["d","d (Decode)"],["e","e (Encode)"],["i","i (Raw Dump)"]],
        "Sounds PC": [["e","e (Encode)"],["d","d (Decode)"],["i","i (Info)"],["r","r (Replace)"]],
        "Sounds NSW": [["e","e (Encode)"],["d","d (Decode)"],["i","i (Info)"],["r","r (Replace)"]]
      };

      function updateCommands() {
        let sel = document.getElementById("converter").value;
        let cmdSel = document.getElementById("command");
        cmdSel.innerHTML = "";
        COMMAND_SETS[sel].forEach(c=>{
            let o=document.createElement("option");
            o.value=c[0];
            o.textContent=c[1];
            cmdSel.appendChild(o);
        });
      }

      window.onload = updateCommands;
    </script>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
