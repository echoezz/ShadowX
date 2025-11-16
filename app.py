from flask import Flask, render_template, request, jsonify
import os
import json
import requests
import shutil

import tempfile

# app = Flask(__name__)
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure Flask to use a custom directory for temporary file storage
app.config["UPLOAD_FOLDER"] = "/home/kali/ShadowX/uploadedFiles"
tempfile.tempdir = app.config["UPLOAD_FOLDER"]

# RPC configuration for the Monero daemon on VM1
MONERO_RPC_URL = "http://192.168.177.149:38081/json_rpc"

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
    """
    Handles file uploads and fetches the latest block height after successful processing.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate file extension
    ALLOWED_EXTENSIONS = {"mdb"}
    if not file.filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file type. Only .mdb files are allowed."}), 400

    try:
        # Save the uploaded file to the configured upload folder
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        # Read the file content from disk
        with open(file_path, "rb") as f:
            raw_tx_content = f.read()  # Read the file as binary
        raw_tx_hex = raw_tx_content.hex()  # Convert binary to hexadecimal

        # Prepare the payload for the Monero RPC `send_raw_transaction` method
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "send_raw_transaction",
            "params": {
                "tx_as_hex": raw_tx_hex,
                "do_not_relay": False
            }
        }
        headers = {"Content-Type": "application/json"}

        # Send the raw transaction to the Monero daemon
        response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers)

        # Delete the temporary file after processing
        os.remove(file_path)

        # Check the response from the Monero daemon
        if response.status_code == 200:
            rpc_result = response.json()
            if "result" in rpc_result and rpc_result["result"].get("status") == "OK":
                # Transaction broadcasted successfully; fetch the block height
                block_height = fetch_block_height()
                if block_height:
                    return jsonify({
                        "message": "Transaction broadcasted successfully",
                        "latest_block_height": block_height
                    }), 200
                else:
                    return jsonify({
                        "message": "Transaction broadcasted successfully",
                        "error": "Failed to fetch block height"
                    }), 200
            else:
                error_message = rpc_result.get("error", {}).get("message", "Unknown error")
                return jsonify({"error": f"Failed to broadcast transaction: {error_message}"}), 400
        else:
            return jsonify({"error": f"Failed to connect to Monero daemon: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def fetch_block_height():
    """
    Fetch the latest block height from the Monero daemon.
    """
    try:
        # Prepare the payload for the Monero RPC `get_block_count` method
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "get_block_count"
        }
        headers = {"Content-Type": "application/json"}

        # Send the request to the Monero daemon
        response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            rpc_result = response.json()
            if "result" in rpc_result:
                return rpc_result["result"]["count"] - 1  # Return block height
        return None
    except Exception as e:
        print(f"Failed to fetch block height: {str(e)}")
        return None


@app.route("/latest_block_height", methods=["GET"])
def get_latest_block_height():
    """
    Fetch and return the current blockchain height.
    """
    block_height = fetch_block_height()
    if block_height is not None:
        return jsonify({"latest_block_height": block_height}), 200
    else:
        return jsonify({"error": "Failed to fetch block height"}), 500

@app.route("/block_info", methods=["GET"])
def get_block_info():
    """
    Fetch and return block information based on block height or block hash.
    """
    query = request.args.get("query", "").strip()  # Get user input from query parameter

    if not query:
        return jsonify({"error": "No block height or hash provided"}), 400

    try:
        # Determine if input is block height (numeric) or block hash (hexadecimal string)
        if query.isdigit():
            # Query is a block height
            payload = {
                "jsonrpc": "2.0",
                "id": "0",
                "method": "get_block_header_by_height",
                "params": {"height": int(query)}
            }
        else:
            # Query is a block hash
            payload = {
                "jsonrpc": "2.0",
                "id": "0",
                "method": "get_block_header_by_hash",
                "params": {"hash": query}
            }
        
        headers = {"Content-Type": "application/json"}

        # Send the request to the Monero daemon
        response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            rpc_result = response.json()
            if "result" in rpc_result:
                # Extract block header information
                block_header = rpc_result["result"]["block_header"]
                # Return detailed block information
                return jsonify({
                    "height": block_header["height"],
                    "hash": block_header["hash"],
                    "timestamp": block_header["timestamp"],
                    "size": block_header.get("block_size", "Unknown"),  # Size may not always be available
                    "difficulty": block_header["difficulty"],
                    "cumulative_difficulty": block_header.get("cumulative_difficulty", "Unknown"),
                    "major_version": block_header.get("major_version", "Unknown"),
                    "minor_version": block_header.get("minor_version", "Unknown"),
                    "nonce": block_header["nonce"],
                    "miner_reward": block_header.get("reward", "Unknown")  # Reward may not always be available
                }), 200
            else:
                return jsonify({"error": "Block not found"}), 404
        else:
            return jsonify({"error": f"Failed to connect to Monero daemon: {response.status_code}"}), 500

    except Exception as e:
        print(f"Error fetching block information: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)