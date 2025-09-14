import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

# import our OCR function
from ocr_core import ocr_core

# define the folder to store uploaded images
UPLOAD_FOLDER = os.path.join('static', 'uploads')

# allow files of a specific type
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# function to check the file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# route for home page (optional, can redirect to /upload)
@app.route('/')
def home_page():
    return redirect(url_for('upload_page'))

# route to handle upload and OCR
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        # check if a file is part of the request
        if 'file' not in request.files:
            return render_template('upload.html', msg='No file selected')

        file = request.files['file']

        # if no file is selected
        if file.filename == '':
            return render_template('upload.html', msg='No file selected')

        # if the file is allowed
        if file and allowed_file(file.filename):
            # secure the filename
            filename = secure_filename(file.filename)

            # save the file to uploads folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # run OCR on the saved file
            extracted_text = ocr_core(file_path)

            # path to show the image in HTML
            img_src = f'/static/uploads/{filename}'

            return render_template('upload.html',
                                   msg='Successfully processed',
                                   extracted_text=extracted_text,
                                   img_src=img_src)

        else:
            return render_template('upload.html', msg='File type not allowed')

    # GET request just shows the form
    return render_template('upload.html')


if __name__ == '__main__':
    # debug=True helps to auto-reload the server on changes
    app.run(debug=True)
