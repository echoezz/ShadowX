from flask import Flask, render_template, request, jsonify
import os

# app = Flask(__name__)
app = Flask(__name__, static_folder='static', static_url_path='/static')

# directory to save uploaded files
upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploadedFiles")
# make sure the upload folder exists
os.makedirs(upload_folder, exist_ok=True)
app.config['upload_folder'] = upload_folder

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tables")
def tables():
    return render_template("tables.html")

@app.route("/charts")
def charts():
    return render_template("charts.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file:
        # Save the file to the upload folder
        filepath = os.path.join(app.config["upload_folder"], file.filename)
        file.save(filepath)
        return jsonify({"message": "File uploaded successfully", "path": filepath}), 200


if __name__ == "__main__":
    app.run(debug=True)