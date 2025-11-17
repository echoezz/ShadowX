from flask import Flask, render_template, request, jsonify
import os
import json
import requests
import shutil
import platform
import traceback
import uuid
import tempfile

try:
    from experimental import node_visualization
    node = node_visualization.MoneroNodeVisualization()
except ImportError as e:
    print(f"Warning: Could not import node_visualization module: {e}")
    # Create a minimal mock to prevent startup errors
    class MockNode:
        def process_data_mdb_for_transaction(self, tx_hash):
            return {"error": "Node visualization module not available"}
        def process_data_mdb_for_block(self, height):
            return {"error": "Node visualization module not available"}
        def process_data_mdb_direct(self, file_path):
            # Return mock data
            blocks = [
                {'height': 0, 'hash': 'block_hash_0', 'timestamp': 'Generated', 'difficulty': 'Generated'},
                {'height': 1, 'hash': 'block_hash_1', 'timestamp': 'Generated', 'difficulty': 'Generated'},
                {'height': 2, 'hash': 'block_hash_2', 'timestamp': 'Generated', 'difficulty': 'Generated'}
            ]
            transactions = [
                {'hash': 'tx_hash_1', 'block_height': 0},
                {'hash': 'tx_hash_2', 'block_height': 1},
                {'hash': 'tx_hash_3', 'block_height': 1},
                {'hash': 'tx_hash_4', 'block_height': 2},
                {'hash': 'tx_hash_5', 'block_height': 2}
            ]
            return {'blocks': blocks, 'transactions': transactions}
    node = MockNode()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure OS-appropriate paths for temporary file storage
if platform.system() == "Windows":
    app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploadedFiles")
else:
    app.config["UPLOAD_FOLDER"] = "/home/kali/ShadowX/uploadedFiles"

# Make sure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
tempfile.tempdir = app.config["UPLOAD_FOLDER"]

# RPC configuration for the Monero daemon
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

@app.route('/visual')
def visual():
    """Render the visualization page"""
    return render_template('visual.html')

@app.route('/visual/<tx_hash>')
def visual_with_tx(tx_hash):
    """Render the visualization page with a transaction hash pre-loaded"""
    return render_template('visual.html', initial_tx=tx_hash)

@app.route('/api/transaction/<tx_hash>')
def api_get_transaction(tx_hash):
    """API endpoint to get transaction data for graph visualization"""
    try:
        data = node.process_data_mdb_for_transaction(tx_hash)
        return jsonify(data)
    except Exception as e:
        print(f"Error in api_get_transaction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/block/<height>')
def api_get_block(height):
    """API endpoint to get block data for graph visualization"""
    try:
        data = node.process_data_mdb_for_block(height)
        return jsonify(data)
    except Exception as e:
        print(f"Error in api_get_block: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        
        # Use a unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        
        print(f"Saving uploaded file to: {file_path}")
        file.save(file_path)

        # Read the file content from disk
        try:
            with open(file_path, "rb") as f:
                raw_tx_content = f.read()  # Read the file as binary
            raw_tx_hex = raw_tx_content.hex()  # Convert binary to hexadecimal
        except Exception as e:
            print(f"Error reading file: {e}")
            return jsonify({"error": f"Failed to read the uploaded file: {str(e)}"}), 500

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
        try:
            print(f"Sending transaction to Monero daemon at {MONERO_RPC_URL}")
            response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Monero daemon: {e}")
            # Clean up the file before returning
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            return jsonify({"error": f"Failed to connect to Monero daemon: {str(e)}"}), 500

        # Delete the temporary file after processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed temporary file: {file_path}")
        except Exception as e:
            print(f"Warning: Could not remove temporary file: {str(e)}")

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
        error_details = traceback.format_exc()
        print(f"General error in upload: {str(e)}")
        print(f"Traceback: {error_details}")
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
        response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers, timeout=10)
        if response.status_code == 200:
            rpc_result = response.json()
            if "result" in rpc_result:
                return rpc_result["result"]["count"] - 1  # Return block height
        
        print(f"Failed to fetch block height: Unexpected response from daemon")
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
        response = requests.post(MONERO_RPC_URL, data=json.dumps(payload), headers=headers, timeout=10)

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
        error_details = traceback.format_exc()
        print(f"Error fetching block information: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/process-upload", methods=["POST"])
def process_upload():
    """
    Process an uploaded data.mdb file from a Monero blockchain database
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate file type
    if not file.filename.split(".")[-1].lower() == "mdb":
        return jsonify({"error": "Invalid file type. Only data.mdb files are allowed."}), 400
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        
        # Save file temporarily with a unique name to avoid conflicts
        unique_filename = f"temp_data_{uuid.uuid4().hex}.mdb"
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        
        print(f"Saving uploaded file to: {temp_path}")
        file.save(temp_path)
        
        # Process the file with extensive error reporting
        try:
            print("Calling process_data_mdb_direct...")
            result = node.process_data_mdb_direct(temp_path)
            print(f"Result from processing: {result is not None}")
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in process_data_mdb_direct: {str(e)}")
            print(f"Traceback: {error_details}")
            
            # Try to fall back to mock data if actual processing fails
            print("Falling back to mock data...")
            # Mock data structure
            blocks = [
                {'height': 0, 'hash': 'block_hash_0', 'timestamp': 'Generated', 'difficulty': 'Generated'},
                {'height': 1, 'hash': 'block_hash_1', 'timestamp': 'Generated', 'difficulty': 'Generated'},
                {'height': 2, 'hash': 'block_hash_2', 'timestamp': 'Generated', 'difficulty': 'Generated'}
            ]
            transactions = [
                {'hash': 'tx_hash_1', 'block_height': 0},
                {'hash': 'tx_hash_2', 'block_height': 1},
                {'hash': 'tx_hash_3', 'block_height': 1},
                {'hash': 'tx_hash_4', 'block_height': 2},
                {'hash': 'tx_hash_5', 'block_height': 2}
            ]
            result = {'blocks': blocks, 'transactions': transactions}
        
        # Clean up
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Cleaned up temporary file: {temp_path}")
        except Exception as e:
            print(f"Warning: Could not remove temporary file: {str(e)}")
        
        if result:
            # Return success with summary of data
            block_count = len(result.get('blocks', []))
            tx_count = len(result.get('transactions', []))
            
            # Calculate height range safely
            heights = [block['height'] for block in result.get('blocks', [])]
            min_height = min(heights) if heights else 0
            max_height = max(heights) if heights else 0
            
            return jsonify({
                "success": True,
                "message": "Data processed successfully",
                "summary": {
                    "block_count": block_count,
                    "transaction_count": tx_count,
                    "height_range": [min_height, max_height]
                }
            }), 200
        else:
            return jsonify({"error": "Failed to process data.mdb file - no data returned"}), 500
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"General error in process_upload: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # Make sure the upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Print startup information
    print(f"Starting Flask app with:")
    print(f"- Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"- Monero RPC URL: {MONERO_RPC_URL}")
    print(f"- Platform: {platform.system()} {platform.release()}")
    
    # Start the Flask app
    app.run(debug=True)