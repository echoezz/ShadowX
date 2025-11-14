from flask import Flask, render_template

# app = Flask(__name__)
app = Flask(__name__, static_folder='static', static_url_path='/static')


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tables")
def tables():
    return render_template("tables.html")

@app.route("/charts")
def charts():
    return render_template("charts.html")

if __name__ == "__main__":
    app.run(debug=True)