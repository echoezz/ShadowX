from flask import Flask, render_template, request, jsonify
import os
import json
import requests
import shutil
import platform
import traceback
import uuid
import tempfile
    

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
MONERO_RPC_URL = "http://127.0.0.1:18081"

try:
    from experimental.node_visualization import MoneroNodeVisualization
    node = MoneroNodeVisualization(rpc_url= "http://127.0.0.1:18081" )
except ImportError as e:
    print(f"Warning: Could not import node_visualization module: {e}")
    # Keep your mock implementation

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
def visual_latest():
    """Render the visualization page with the latest transaction"""
    node = MoneroNodeVisualization(MONERO_RPC_URL)
    
    # Get the latest block height
    info_result = node._make_rpc_call("get_info")
    if "result" not in info_result:
        return render_template('error.html', error="Could not fetch blockchain info")
        
    height = info_result["result"]["height"] - 1  # Get the latest confirmed block
    
    # Get the latest block
    block = node.get_block_by_height(height)
    if "error" in block:
        return render_template('error.html', error=f"Could not fetch block {height}")
    
    # Check if there are any transactions in the block
    tx_hash = None
    if "tx_hashes" in block and len(block["tx_hashes"]) > 0:
        tx_hash = block["tx_hashes"][0]
    else:
        # If no regular transactions, try to find a block with transactions
        for h in range(height-10, height):
            block = node.get_block_by_height(h)
            if "tx_hashes" in block and len(block["tx_hashes"]) > 0:
                tx_hash = block["tx_hashes"][0]
                height = h
                break
    
    if not tx_hash:
        # If still no transactions found, just use the miner tx
        if "miner_tx_hash" in block:
            tx_hash = block["miner_tx_hash"]
        else:
            return render_template('error.html', error="No transactions found in recent blocks")
    
    # Get the transaction data
    tx_data = node.get_transaction(tx_hash)
    if "error" in tx_data:
        return render_template('error.html', error=f"Could not fetch transaction {tx_hash}")
    
    # Add block height to transaction data if not present
    if "block_height" not in tx_data:
        tx_data["block_height"] = height
    
    # Return the visual.html template with the transaction data
    return render_template('visual.html', transaction=tx_data, auto_show_graph=True)

@app.route('/api/check_rpc_status')
def check_rpc_status():
    """Check all required RPC connections and return status"""
    try:
        status = node.check_rpc_connections()
        return jsonify({"success": True, "checks": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/transaction/<tx_hash>')
def display_transaction(tx_hash):
    try:
        # Use the MoneroNodeVisualization class to get transaction data
        tx_data = node.get_transaction(tx_hash)
        
        print(f"Transaction data: {json.dumps(tx_data, indent=2)}")
        
        if "error" in tx_data:
            return render_template('error.html', error=tx_data["error"])
        
        # Parse transaction data for display
        return render_template('visual.html', transaction=tx_data)
    except Exception as e:
        print(f"Exception: {str(e)}")
        return render_template('error.html', error=str(e))
        
@app.route('/api/graph/transaction/<tx_hash>')
def api_graph_transaction(tx_hash):
    node = MoneroNodeVisualization("http://127.0.0.1:18081")
    print(f"API graph request for transaction hash: {tx_hash}")
    result = node.visualize_transaction(tx_hash)
    return jsonify(result)
        
from datetime import datetime

@app.template_filter('timestamp_format')
def timestamp_format(timestamp):
    """Format a Unix timestamp as a human-readable date"""
    if not timestamp:
        return 'Unknown'
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

@app.template_filter('xmr_amount')
def xmr_amount(amount):
    """Format a Monero amount from atomic units to XMR"""
    if amount is None:
        return '0.000000000000'
    return '{:.12f}'.format(float(amount) / 1000000000000)

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
