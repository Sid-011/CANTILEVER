import os
import re
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from markupsafe import Markup, escape

# import your OCR helper (must exist in same folder)
from ocr_core import ocr_core

# If you want the app to call tesseract directly from Python, set this path:
# Update this if your tesseract.exe is somewhere else
TESSERACT_CMD = r"C:\Users\hd c\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# (Optional) If ocr_core uses pytesseract internally, ensure it uses this exe:
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
except Exception:
    # If pytesseract not importable here, ocr_core will import it; ignore
    pass

# Flask app config
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tiff", "bmp", "gif"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def linkify_numbers(text):
    """
    Escape HTML, then convert sequences of digits (3+ digits) into clickable links.
    Links open a Google search for that number in a new tab.
    """
    if not text:
        return Markup("")
    escaped = escape(text)  # prevents HTML injection
    # replace long digit sequences with anchor tags
    def repl(m):
        num = m.group(0)
        url = f"https://www.google.com/search?q={num}"
        return f'<a href="{url}" target="_blank" rel="noopener">{num}</a>'
    linked = re.sub(r'(\d{3,})', repl, escaped)
    # Preserve newlines as <br>
    linked = linked.replace("\n", "<br>\n")
    return Markup(linked)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("index.html", msg="No file part")
        file = request.files["file"]
        if file.filename == "":
            return render_template("index.html", msg="No selected file")
        if not allowed_file(file.filename):
            return render_template("index.html", msg="File type not allowed (png/jpg/jpeg/...)")
        # secure and save
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        # run OCR using your helper function
        try:
            extracted_text = ocr_core(save_path)
        except Exception as e:
            return render_template("index.html", msg=f"OCR failed: {e}")

        # make numbers clickable and preserve line breaks
        extracted_html = linkify_numbers(extracted_text)

        img_src = url_for("static", filename=f"uploads/{filename}")
        return render_template("index.html",
                               msg="Successfully processed",
                               extracted_text=extracted_text,
                               extracted_html=extracted_html,
                               img_src=img_src)
    # GET
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
