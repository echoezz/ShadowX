from flask import Flask, render_template, request, jsonify
import os
import json
import requests
import shutil
import platform
import traceback
import uuid
import tempfile
import subprocess
from experimental.node_visualization import MoneroNodeVisualization

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

# Initialize visualization module
node = MoneroNodeVisualization()

# Global variable to store monerod process information
monerod_process_data = {"process": None, "rpc_port": None}

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
    """Render the visualization page with the most recent transaction blocks"""
    # Default to showing 20 latest blocks containing transactions
    count = request.args.get('count', 20, type=int)
    return render_template('visual.html', view_type="recent_tx_blocks", count=count)

# Function to start monero service (for inbuilt to web app)
def start_monerod(base_dir, rpc_port=38081):
    """
    Start the Monero daemon in stagenet mode using the provided data.mdb file.
    """
    try:
        # monerod path
        monerod_path = "/home/kali/ShadowX/monero-x86_64-linux-gnu-v0.18.4.4/monerod"

        # Build the monerod command
        command = [
            monerod_path,
            "--stagenet",
            "--data-dir", base_dir,
            "--rpc-bind-ip", "127.0.0.1",
            "--rpc-bind-port", str(rpc_port),
            "--non-interactive",
            "--confirm-external-bind"
        ]
        print(f"Starting monerod with command: {' '.join(command)}")
        print("data_dir:", base_dir)
        # Start the process
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        # wait briefly to ensure daemon starts and creates the lock.mdb
        import time
        time.sleep(5)
    
        # Check for lock.mdb in the correct location
        stagenet_dir = os.path.join(base_dir, "stagenet")
        lock_mdb_path = os.path.join(stagenet_dir, "lmdb", "lock.mdb")
        if not os.path.exists(lock_mdb_path):
             raise RuntimeError(f"lock.mdb file was not created in {os.path.join(stagenet_dir, 'lmdb')}")
    
        # Return process details
        return {"process": process, "rpc_port": rpc_port}
    except Exception as e:
        print(f"Error starting monerod: {str(e)}")
        return None

# To start monero stagenet service from web app directly after user press button to start
@app.route("/start-service", methods=["POST"])
def start_monero_service():
    """
    Start the Monero daemon service and return the RPC URL.
    """
    global monerod_process_data
    try:
        # Directory to store the blockchain data
        base_dir = app.config["UPLOAD_FOLDER"]
        stagenet_dir = os.path.join(base_dir, "stagenet")
        lmdb_dir = os.path.join(stagenet_dir, "lmdb")
        data_mdb_path = os.path.join(lmdb_dir, "data.mdb")
        
        if not os.path.exists(data_mdb_path):
            return jsonify({"error": "data.mdb file is missing in the stagenet directory."}), 400
    
        # Get the RPC port from the request or default to 38081
        request_data = request.get_json() or {}
        rpc_port = request.json.get("rpc_port", 38081)
        # Start monerod
        monerod_process = start_monerod(base_dir, rpc_port)

        if monerod_process:
            # Store the process details
            monerod_process_data["process"] = monerod_process["process"]
            monerod_process_data["rpc_port"] = monerod_process["rpc_port"]

            return jsonify({
                "message": "Monero service started successfully.",
                "rpc_url": f"http://127.0.0.1:{monerod_process['rpc_port']}/json_rpc",
            }), 200
        else:
            return jsonify({"error": "Failed to start Monero service."}), 500

    except Exception as e:
        print(f"Error in start_monero_service: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# End monero stagenet service
@app.route('/end-service', methods=["POST"])
def end_service():
    """
    Stop the Monero daemon service.
    """
    global monerod_process_data

    # Check if a process is running
    if monerod_process_data["process"] is None:
        return jsonify({"error": "No Monero service is currently running."}), 400

    try:
        # Terminate the process
        process = monerod_process_data["process"]
        process.terminate()
        process.wait(timeout=10)  # Wait for up to 10 seconds for the process to terminate
        print("Monero service stopped successfully.")

        # Clear the process data
        monerod_process_data = {"process": None, "rpc_port": None}
        return jsonify({"message": "Monero service stopped successfully."}), 200
    except subprocess.TimeoutExpired:
        # If the process did not terminate, kill it
        process.kill()
        monerod_process_data = {"process": None, "rpc_port": None}
        return jsonify({"message": "Monero service forcefully stopped."}), 200
    except Exception as e:
        print(f"Error stopping Monero service: {str(e)}")
        return jsonify({"error": f"Failed to stop Monero service: {str(e)}"}), 500

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ALLOWED_EXTENSIONS = {"mdb"}
    if not file.filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file type. Only .mdb files are allowed."}), 400

    try:
        # Ensure the upload folder exists
        stagenet_dir = os.path.join(app.config["UPLOAD_FOLDER"], "stagenet")
        lmdb_dir = os.path.join(stagenet_dir, "lmdb")
        os.makedirs(lmdb_dir, exist_ok=True)
        
        # Save the uploaded file as data.mdb in the stagenet directory
        data_mdb_path = os.path.join(lmdb_dir, "data.mdb")
        file.save(data_mdb_path)
        print(f"Uploaded data.mdb saved to: {data_mdb_path}")

        # Return success response
        return jsonify({"message": "File uploaded successfully", "path": data_mdb_path}), 200
    
    except Exception as e:
        print(f"Error in upload: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/get-block", methods=["POST"])
def get_block():
    """
    Get block information by height using the running Monero daemon's RPC.
    """
    global monerod_process_data
     # Check if Monero service is running
    if monerod_process_data["process"] is None or monerod_process_data["rpc_port"] is None:
        return jsonify({"error": "Monero service is not running. Please start the service first."}), 400
    try:
        # Get block height from request
        data = request.get_json()
        block_height = data.get("height")
        if block_height is None:
            return jsonify({"error": "Block height is required"}), 400
        # Validate block height is a number
        try:
            block_height = int(block_height)
        except ValueError:
            return jsonify({"error": "Block height must be a valid number"}), 400
        # Build RPC URL using the stored port
        rpc_url = f"http://127.0.0.1:{monerod_process_data['rpc_port']}/json_rpc"
        # Prepare RPC request payload
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "get_block",
            "params": {
                "height": block_height
            }
        }
        # Make RPC call to monerod
        response = requests.post(rpc_url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            # Check for RPC errors
            if "error" in result:
                return jsonify({"error": f"RPC error: {result['error'].get('message', 'Unknown error')}"}), 500
            # Extract block information
            block_data = result.get("result", {})
            block_header = block_data.get("block_header", {})
            # Format the response
            formatted_response = {
                "block_height": block_header.get("height"),
                "block_hash": block_header.get("hash"),
                "timestamp": block_header.get("timestamp"),
                "size": block_header.get("block_size"),
                "difficulty": block_header.get("difficulty"),
                "cumulative_difficulty": block_header.get("cumulative_difficulty"),
                "major_version": block_header.get("major_version"),
                "minor_version": block_header.get("minor_version"),
                "nonce": block_header.get("nonce"),
                "reward": block_header.get("reward"),
                "num_txes": block_header.get("num_txes", 0),
                "orphan_status": block_header.get("orphan_status", False)
            }
            return jsonify(formatted_response), 200
        else:
            return jsonify({"error": f"Failed to connect to Monero RPC. Status code: {response.status_code}"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Monero daemon timed out"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Monero daemon. Is it running?"}), 500
    except Exception as e:
        print(f"Error in get_block: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/transaction/<tx_hash>')
def api_get_transaction(tx_hash):
    """API endpoint to get transaction data with decoy information"""
    global monerod_process_data
    try:
        if monerod_process_data["process"] is None or monerod_process_data["rpc_port"] is None:
            return jsonify({"error": "Monero service is not running. Please start the service first."}), 400
            
        # Remove tx_ prefix if present
        if tx_hash.startswith('tx_'):
            tx_hash = tx_hash[3:]
        
        # Use the exact format that works in your curl command
        rpc_url = f"http://127.0.0.1:{monerod_process_data['rpc_port']}/get_transactions"
        payload = {
            "txs_hashes": [tx_hash],
            "decode_as_json": True
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(rpc_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"error": f"Failed to get transaction data. Status code: {response.status_code}"}), 500
            
        result = response.json()
        if "txs" not in result or not result["txs"]:
            return jsonify({"error": "Transaction not found"}), 404
            
        tx_data = result["txs"][0]
        
        # Parse the transaction JSON
        tx_json = None
        if "as_json" in tx_data:
            try:
                tx_json = json.loads(tx_data["as_json"])
            except json.JSONDecodeError:
                return jsonify({"error": "Failed to parse transaction JSON"}), 500
                
        if not tx_json:
            return jsonify({"error": "Transaction data is incomplete"}), 500
        
        # Extract ring signature information for inputs
        ring_members = []
        for i, vin in enumerate(tx_json.get("vin", [])):
            if "key" in vin:
                key_image = vin["key"].get("k_image", "")
                key_offsets = vin["key"].get("key_offsets", [])
                
                # Get absolute offsets from relative offsets
                absolute_offsets = []
                running_total = 0
                for offset in key_offsets:
                    running_total += offset
                    absolute_offsets.append(running_total)
                
                ring_members.append({
                    "input_index": i,
                    "key_image": key_image,
                    "relative_offsets": key_offsets,
                    "absolute_offsets": absolute_offsets
                })
        
        # Create a response with all necessary fields including ring data
        return jsonify({
            "hash": tx_hash,
            "block_height": tx_data.get("block_height"),
            "fee": tx_json.get("rct_signatures", {}).get("txnFee"),
            "size": tx_data.get("size") or tx_data.get("blob_size"),
            "inputs": len(tx_json.get("vin", [])),
            "outputs": len(tx_json.get("vout", [])),
            "version": tx_json.get("version"),
            "unlock_time": tx_json.get("unlock_time"),
            "ring_signatures": ring_members,
            # Add output details for visualization
            "outputs_data": [
                {
                    "index": i,
                    "amount": output.get("amount", 0),
                    "target": output.get("target", {})
                } for i, output in enumerate(tx_json.get("vout", []))
            ]
        })
    except Exception as e:
        print(f"Error in api_get_transaction: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/transaction-blocks/<int:count>')
def api_transaction_blocks(count=20):
    """API endpoint to get blocks containing transactions"""
    global monerod_process_data
    
    # Check if Monero service is running
    if monerod_process_data["process"] is None or monerod_process_data["rpc_port"] is None:
        return jsonify({"error": "Monero service is not running"}), 400
        
    try:
        # Get transaction blocks
        graph_data = node.process_recent_transaction_blocks(count, monerod_process_data["rpc_port"])
        return jsonify(graph_data)
        
    except Exception as e:
        print(f"Error fetching transaction blocks: {str(e)}")
        return jsonify({"error": str(e)}), 500


# route for get_transactions
@app.route('/get-transactions', methods=['POST'])
def get_transactions():
    data = request.get_json()
    txs_hashes = data.get('txs_hashes', [])
    
    if not txs_hashes:
        return jsonify({'error': 'No transaction hashes provided'}), 400
    
    payload = {
        'txs_hashes': txs_hashes,
        'decode_as_json': True
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:38081/get_transactions',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # Make sure the upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Print startup information
    print(f"Starting Flask app with:")
    print(f"- Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"- Platform: {platform.system()} {platform.release()}")
    
    # Start the Flask app
    app.run(debug=True)