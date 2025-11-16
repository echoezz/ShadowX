from flask import Flask, render_template, request, jsonify
import os
import json
import requests
import shutil

# app = Flask(__name__)
app = Flask(__name__, static_folder='static', static_url_path='/static')

# RPC configuration for the Monero daemon on VM1
MONERO_RPC_URL = "http://192.168.177.150:38081/json_rpc"

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
    ALLOWED_EXTENSIONS = {"mdb"}

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate file type
    if not file.filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file type. Only data.mdb files are allowed."}), 400
    
    try:
        # Read file content directly into memory
        raw_tx_content = file.read()  # Read the file as binary
        raw_tx_hex = raw_tx_content.hex()  # Convert binary to hexadecimal

        # Prepare the payload for the Monero RPC `send_raw_transaction` method
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "send_raw_transaction",
            "params": {
                "tx_as_hex": raw_tx_hex,
                "do_not_relay": False
            }
        }

        # Send the raw transaction to the Monero daemon on VM1
        response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers)

        # Parse and return the response from the Monero daemon
        if response.status_code == 200:
            rpc_result = response.json()
            if "result" in rpc_result and rpc_result["result"].get("status") == "OK":
                return jsonify({"message": "Transaction broadcasted successfully"}), 200
            else:
                # Handle errors reported by the Monero daemon
                error_message = rpc_result.get("error", {}).get("message", "Unknown error")
                return jsonify({"error": f"Failed to broadcast transaction: {error_message}"}), 400
        else:
            # Handle HTTP errors
            return jsonify({"error": f"Failed to connect to Monero daemon: {response.status_code}"}), 500

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)