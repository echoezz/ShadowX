import json
import requests
import time

class MoneroNodeVisualization:
    def __init__(self):
        # Default values
        self.max_depth = 3  # Maximum depth for transaction visualization
        self.max_ring_size = 16  # Maximum number of ring members to show
    
    def process_transaction_for_graph(self, tx_json, tx_hash, block_height):
        """Process a transaction and prepare data for graph visualization"""
        nodes = []
        links = []
        
        # Add transaction node
        tx_id = f"tx_{tx_hash}"
        nodes.append({
            "id": tx_id,
            "type": "transaction",
            "hash": tx_hash,
            "block_height": block_height
        })
        
        # Process inputs
        if "vin" in tx_json:
            for i, vin in enumerate(tx_json["vin"]):
                if "key" in vin:
                    # Add input node
                    input_id = f"{tx_id}_in_{i}"
                    nodes.append({
                        "id": input_id,
                        "type": "input",
                        "key_image": vin["key"].get("k_image", "")
                    })
                    
                    # Link input to transaction
                    links.append({
                        "source": input_id,
                        "target": tx_id,
                        "type": "input"
                    })
                    
                    # Process ring members
                    if "key_offsets" in vin["key"]:
                        # Calculate absolute indices
                        absolute_indices = []
                        current_idx = 0
                        for offset in vin["key"]["key_offsets"]:
                            current_idx += offset
                            absolute_indices.append(current_idx)
                        
                        # Add ring members (limit to max_ring_size if needed)
                        for j, abs_idx in enumerate(absolute_indices[:self.max_ring_size]):
                            ring_id = f"{input_id}_ring_{j}"
                            nodes.append({
                                "id": ring_id,
                                "type": "ring_member",
                                "absolute_index": abs_idx
                            })
                            
                            # Link ring member to input
                            links.append({
                                "source": ring_id,
                                "target": input_id,
                                "type": "ring_member"
                            })
        
        # Process outputs
        if "vout" in tx_json:
            for i, vout in enumerate(tx_json["vout"]):
                output_key = None
                if "target" in vout:
                    if "key" in vout["target"]:
                        output_key = vout["target"]["key"]
                    elif "tagged_key" in vout["target"]:
                        output_key = vout["target"]["tagged_key"]["key"]
                
                if output_key:
                    # Add output node
                    output_id = f"{tx_id}_out_{i}"
                    nodes.append({
                        "id": output_id,
                        "type": "output",
                        "key": output_key,
                        "amount": vout.get("amount", 0)
                    })
                    
                    # Link transaction to output
                    links.append({
                        "source": tx_id,
                        "target": output_id,
                        "type": "output"
                    })
        
        return {
            "nodes": nodes,
            "links": links,
            "transaction": {
                "tx_hash": tx_hash,
                "block_height": block_height,
                "tx_json": tx_json
            }
        }
    
    def fetch_transaction_with_rings(self, tx_hash, rpc_port=38081):
        """Fetch detailed transaction data including ring signatures"""
        try:
            # Use the get_transactions endpoint directly
            rpc_url = f"http://127.0.0.1:{rpc_port}/get_transactions"
            payload = {
                "txs_hashes": [tx_hash],
                "decode_as_json": True
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(rpc_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
                
            result = response.json()
            if "txs" not in result or not result["txs"]:
                return None
                
            tx_data = result["txs"][0]
            
            # Parse the transaction JSON
            tx_json = None
            if "as_json" in tx_data:
                try:
                    tx_json = json.loads(tx_data["as_json"])
                except json.JSONDecodeError:
                    return None
                    
            if not tx_json:
                return None
            
            # Extract ring signature information for inputs
            ring_signatures = []
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
                    
                    ring_signatures.append({
                        "input_index": i,
                        "key_image": key_image,
                        "relative_offsets": key_offsets,
                        "absolute_offsets": absolute_offsets
                    })
            
            # Create a response with all necessary fields including ring data
            return {
                "hash": tx_hash,
                "block_height": tx_data.get("block_height"),
                "fee": tx_json.get("rct_signatures", {}).get("txnFee"),
                "size": tx_data.get("size") or tx_data.get("blob_size"),
                "inputs": len(tx_json.get("vin", [])),
                "outputs": len(tx_json.get("vout", [])),
                "version": tx_json.get("version"),
                "unlock_time": tx_json.get("unlock_time"),
                "ring_signatures": ring_signatures,
                "outputs_data": [
                    {
                        "index": i,
                        "amount": output.get("amount", 0),
                        "target": output.get("target", {})
                    } for i, output in enumerate(tx_json.get("vout", []))
                ]
            }
        except Exception as e:
            print(f"Error fetching transaction with rings: {str(e)}")
            return None
    
    def process_recent_transaction_blocks(self, count=20, rpc_port=38081):
        """Process only blocks that contain transactions (not just mining rewards)"""
        try:
            # Build RPC URL
            rpc_url = f"http://127.0.0.1:{rpc_port}/json_rpc"
            
            # Get current blockchain height
            info_payload = {
                "jsonrpc": "2.0",
                "id": "0",
                "method": "get_info"
            }
            
            info_response = requests.post(rpc_url, json=info_payload, timeout=10)
            if info_response.status_code != 200:
                return {"error": "Failed to get blockchain info"}
                
            height = info_response.json().get("result", {}).get("height", 0)
            
            # Start from recent blocks and work backwards
            blocks_with_tx = []
            current_height = height - 1  # Start from the latest block
            
            # Keep fetching blocks until we have enough with transactions
            while len(blocks_with_tx) < count and current_height > 0:
                block_payload = {
                    "jsonrpc": "2.0",
                    "id": "0",
                    "method": "get_block",
                    "params": {"height": current_height}
                }
                
                block_response = requests.post(rpc_url, json=block_payload, timeout=10)
                if block_response.status_code == 200:
                    block_data = block_response.json().get("result", {})
                    
                    # Check if this block has transactions (not just coinbase)
                    if "tx_hashes" in block_data and block_data["tx_hashes"]:
                        blocks_with_tx.append({
                            "height": current_height,
                            "hash": block_data.get("block_header", {}).get("hash", ""),
                            "timestamp": block_data.get("block_header", {}).get("timestamp", 0),
                            "tx_count": len(block_data["tx_hashes"]),
                            "tx_hashes": block_data["tx_hashes"]
                        })
                
                current_height -= 1
                
            # Now process these blocks into a graph
            return self.create_transaction_blocks_graph(blocks_with_tx, rpc_port)
        
        except Exception as e:
            print(f"Error fetching transaction blocks: {str(e)}")
            return {"error": str(e)}
    
    def create_transaction_blocks_graph(self, blocks, rpc_port):
        """Create a graph visualization from transaction blocks"""
        nodes = []
        links = []
        
        # Add block nodes
        for block in blocks:
            block_id = f"block_{block['height']}"
            nodes.append({
                "id": block_id,
                "type": "block",
                "height": block["height"],
                "hash": block["hash"],
                "timestamp": block["timestamp"],
                "tx_count": block["tx_count"]
            })
            
            # Add transaction nodes for this block (limited to first 5 per block for performance)
            for i, tx_hash in enumerate(block["tx_hashes"][:5]):
                # Fetch detailed transaction data with rings
                tx_data = self.fetch_transaction_with_rings(tx_hash, rpc_port)
                
                if tx_data:
                    tx_id = f"tx_{tx_hash}"
                    nodes.append({
                        "id": tx_id,
                        "type": "transaction",
                        "hash": tx_hash,
                        "block_height": block["height"],
                        "details": tx_data  # Include the full details
                    })
                    
                    # Link block to transaction
                    links.append({
                        "source": block_id,
                        "target": tx_id,
                        "type": "contains"
                    })
                    
                    # Add key images and ring members
                    if "ring_signatures" in tx_data and tx_data["ring_signatures"]:
                        for ring_info in tx_data["ring_signatures"]:
                            # Create key image node
                            key_image = ring_info["key_image"]
                            key_image_id = f"ki_{key_image[:8]}"
                            
                            nodes.append({
                                "id": key_image_id,
                                "type": "keyimage",
                                "key_image": key_image,
                                "input_index": ring_info["input_index"]
                            })
                            
                            # Link transaction to key image
                            links.append({
                                "source": tx_id,
                                "target": key_image_id,
                                "type": "input"
                            })
                            
                            # Add ring members (decoys)
                            if "absolute_offsets" in ring_info:
                                for offset_idx, offset in enumerate(ring_info["absolute_offsets"]):
                                    ring_id = f"{key_image_id}_ring_{offset_idx}"
                                    
                                    nodes.append({
                                        "id": ring_id,
                                        "type": "ring_member",
                                        "absolute_offset": offset,
                                        "position": offset_idx
                                    })
                                    
                                    # Link ring member to key image
                                    links.append({
                                        "source": ring_id,
                                        "target": key_image_id,
                                        "type": "ring"
                                    })
                    
                    # Add output nodes
                    if "outputs_data" in tx_data:
                        for output in tx_data["outputs_data"]:
                            output_id = f"{tx_id}_out_{output['index']}"
                            
                            nodes.append({
                                "id": output_id,
                                "type": "output",
                                "index": output["index"],
                                "amount": output["amount"]
                            })
                            
                            # Link transaction to output
                            links.append({
                                "source": tx_id,
                                "target": output_id,
                                "type": "output"
                            })
        
        return {
            "nodes": nodes,
            "links": links,
            "blocks": blocks
        }