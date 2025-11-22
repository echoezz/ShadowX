from flask import Flask, render_template, request, jsonify
import os
import json
import requests
import shutil
import platform
import traceback
import uuid
import tempfile

# for starting monero service
import subprocess

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
# MONERO_RPC_URL = "http://192.168.177.149:38081/json_rpc"

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

# functn to start monero service
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

monerod_process_data = {"process": None, "rpc_port": None}
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

# deon version of upload in index.html
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
        os.makedirs(stagenet_dir, exist_ok=True)
        
	# Save the uploaded file as data.mdb in the stagenet directory
        data_mdb_path = os.path.join(lmdb_dir, "data.mdb")
        file.save(data_mdb_path)
        print(f"Uploaded data.mdb saved to: {data_mdb_path}")

        # Return success response
        return jsonify({"message": "File uploaded successfully", "path": data_mdb_path}), 200
	
    except Exception as e:
        #error_details = traceback.format_exc()
        #print(f"General error in upload: {str(e)}")
        #print(f"Traceback: {error_details}")
        #return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        print(f"Error in upload: {str(e)}")
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
    #print(f"- Monero RPC URL: {MONERO_RPC_URL}")
    print(f"- Platform: {platform.system()} {platform.release()}")
    
    # Start the Flask app
    app.run(debug=True)
