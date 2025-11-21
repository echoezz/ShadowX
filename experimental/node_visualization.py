import requests
import json
from datetime import datetime

class MoneroNodeVisualization:
    def __init__(self, rpc_url="http://localhost:18081"):
        self.rpc_url = rpc_url
        print(f"Initialized MoneroNodeVisualization with RPC URL: {rpc_url}")
        # Run a startup check
        status = self.check_rpc_connections()
        for method, success in status.items():
            print(f"Initial RPC check - {method}: {'✅' if success else '❌'}")
    
    def _format_timestamp(self, timestamp):
        """Format timestamp as a readable date"""
        if not timestamp:
            return 'Pending'
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

    def _make_rpc_call(self, method, params=None):
        """Make RPC call to Monero daemon with visible feedback"""
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method
        }
        
        if params:
            payload["params"] = params
            
        try:
            print(f"➡️ Making RPC call: {method} to {self.rpc_url}/json_rpc")
            response = requests.post(self.rpc_url + "/json_rpc", json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    print(f"✅ RPC call successful: {method}")
                    return result
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    print(f"❌ RPC call failed: {method} - {error_msg}")
                    return {"error": error_msg}
            else:
                print(f"❌ RPC call failed: {method} - HTTP {response.status_code}")
                return {"error": f"HTTP Error: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            print(f"❌ RPC connection error: Could not connect to {self.rpc_url}")
            return {"error": f"Connection refused to {self.rpc_url}"}
        except Exception as e:
            print(f"❌ RPC call exception ({method}): {str(e)}")
            return {"error": str(e)}
    
    def _make_non_json_rpc_call(self, endpoint, params=None):
        """Make RPC call to non-JSON RPC endpoints with visible feedback"""
        try:
            print(f"➡️ Making non-JSON RPC call: {endpoint} to {self.rpc_url}/{endpoint}")
            # Add proper Content-Type header
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.rpc_url + "/" + endpoint, json=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Non-JSON RPC call successful: {endpoint}")
                return result
            else:
                print(f"❌ Non-JSON RPC call failed: {endpoint} - HTTP {response.status_code}")
                print(f"Response content: {response.text[:200]}...")
                return {"error": f"HTTP Error: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            print(f"❌ RPC connection error: Could not connect to {self.rpc_url}/{endpoint}")
            return {"error": f"Connection refused to {self.rpc_url}/{endpoint}"}
        except Exception as e:
            print(f"❌ Non-JSON RPC call exception ({endpoint}): {str(e)}")
            return {"error": str(e)}

    def check_rpc_connections(self):
        """Test all required RPC endpoints and return status"""
        print("Running RPC connection checks...")
        checks = {
            "get_info": False,
            "get_block": False,
            "get_transactions": False,
            "get_transaction_pool": False
        }
        
        # Test get_info
        info = self._make_rpc_call("get_info")
        if "result" in info:
            checks["get_info"] = True
            
        # Test get_block with height 0 (genesis block)
        block = self._make_rpc_call("get_block", {"height": 0})
        if "result" in block:
            checks["get_block"] = True
        
        # Test transaction pool
        pool = self._make_rpc_call("get_transaction_pool")
        if "result" in pool:
            checks["get_transaction_pool"] = True
        
        # Test get_transactions (might not work without valid tx hashes)
        try:
            print(f"➡️ Testing non-JSON endpoint: get_transactions to {self.rpc_url}/get_transactions")
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.rpc_url + "/get_transactions", json={"txs_hashes":[]}, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ RPC endpoint check successful: get_transactions")
                checks["get_transactions"] = True
            else:
                print(f"❌ RPC endpoint check failed: get_transactions - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ RPC endpoint check exception (get_transactions): {str(e)}")
        
        print("RPC connection check results:")
        for method, success in checks.items():
            print(f"  {method}: {'✅' if success else '❌'}")
        
        return checks

    def get_blockchain_info(self, max_blocks=100):
        """Get blockchain info using RPC calls"""
        print("Getting blockchain info...")
        info_result = self._make_rpc_call("get_info")
        if "result" not in info_result:
            print("❌ Failed to get blockchain info")
            return {"error": "Failed to get blockchain info", "details": info_result}
        
        blockchain_info = info_result["result"]
        height = blockchain_info["height"]
        
        blocks = []
        start_height = max(0, height - max_blocks)
        
        print(f"Fetching blocks from height {start_height} to {height}...")
        for h in range(start_height, height):
            block_data = self.get_block_by_height(h)
            if "error" not in block_data:
                blocks.append(block_data)
        
        mempool_info = self._make_rpc_call("get_transaction_pool")
        
        return {
            "info": blockchain_info,
            "blocks": blocks,
            "mempool": mempool_info.get("result", {})
        }
    
    def get_block_by_height(self, height):
        """Get block data by height"""
        result = self._make_rpc_call("get_block", {"height": height})
        
        if "result" in result:
            block_data = result["result"]
            
            if "block_header" in block_data and "timestamp" in block_data["block_header"]:
                block_data["block_header"]["timestamp_formatted"] = self._format_timestamp(
                    block_data["block_header"]["timestamp"]
                )
            
            block_data["height"] = height
            
            return block_data
        
        return {"error": "Failed to get block", "details": result}
    
    def get_block_by_hash(self, block_hash):
        """Get block data by hash"""
        result = self._make_rpc_call("get_block", {"hash": block_hash})
        
        if "result" in result:
            block_data = result["result"]
            
            if "block_header" in block_data and "timestamp" in block_data["block_header"]:
                block_data["block_header"]["timestamp_formatted"] = self._format_timestamp(
                    block_data["block_header"]["timestamp"]
                )
            
            return block_data
        
        return {"error": "Failed to get block", "details": result}
    
    def get_transactions(self, tx_hashes, decode_as_json=True):
        """Get transaction data by hash"""
        # Format parameters exactly as in the working curl command
        params = {
            "txs_hashes": tx_hashes,
            "decode_as_json": decode_as_json
        }
        
        print(f"Requesting transactions with params: {json.dumps(params)}")
        result = self._make_non_json_rpc_call("get_transactions", params)
        
        if "txs" in result:
            if decode_as_json:
                for tx in result["txs"]:
                    if "tx_json" in tx and isinstance(tx["tx_json"], str):
                        try:
                            tx["tx_json"] = json.loads(tx["tx_json"])
                        except json.JSONDecodeError:
                            print(f"Failed to parse tx_json: {tx['tx_json'][:100]}...")
            return result
        
        print(f"Failed to get transaction data. Response: {json.dumps(result, indent=2)}")
        return {"error": "Failed to get transactions", "details": result}
    
    def get_transaction(self, tx_hash, decode_as_json=True):
        """Get single transaction data by hash"""
        result = self.get_transactions([tx_hash], decode_as_json)
        
        if "error" not in result and "txs" in result and len(result["txs"]) > 0:
            return result["txs"][0]
        
        return {"error": "Transaction not found", "details": result}
    
    def get_block_with_transactions(self, height):
        """Get block with full transaction details"""
        block = self.get_block_by_height(height)
        
        if "error" in block:
            return block
        
        if "tx_hashes" in block and block["tx_hashes"]:
            transactions_result = self.get_transactions(block["tx_hashes"])
            
            if "txs" in transactions_result:
                block["transactions"] = transactions_result["txs"]
            else:
                block["transactions_error"] = transactions_result.get("error", "Unknown error")
        
        if "miner_tx" in block:
            try:
                miner_tx_json = json.loads(block["miner_tx_json"]) if "miner_tx_json" in block else {}
                block["miner_transaction"] = {
                    "tx_hash": block.get("miner_tx_hash", ""),
                    "tx_json": miner_tx_json
                }
            except (json.JSONDecodeError, TypeError):
                block["miner_transaction_error"] = "Failed to parse miner transaction JSON"
        
        return block
    
    def get_mempool_transactions(self, decode_as_json=True):
        """Get mempool transactions"""
        result = self._make_rpc_call("get_transaction_pool")
        
        if "result" in result and "transactions" in result["result"]:
            transactions = result["result"]["transactions"]
            
            if decode_as_json and transactions:
                tx_hashes = [tx["id_hash"] for tx in transactions]
                detailed_txs = self.get_transactions(tx_hashes, decode_as_json)
                
                if "txs" in detailed_txs:
                    tx_details_map = {tx["tx_hash"]: tx for tx in detailed_txs["txs"]}
                    
                    for tx in transactions:
                        tx_hash = tx["id_hash"]
                        if tx_hash in tx_details_map:
                            tx["detailed_json"] = tx_details_map[tx_hash].get("tx_json", {})
            
            return {"transactions": transactions}
        
        return {"error": "Failed to get mempool transactions", "details": result}
    
    def get_network_stats(self):
        """Get network statistics"""
        info = self._make_rpc_call("get_info")
        hard_fork = self._make_rpc_call("hard_fork_info")
        connections = self._make_rpc_call("get_connections")
        mining = self._make_rpc_call("mining_status")
        fee = self._make_rpc_call("get_fee_estimate")
        
        return {
            "info": info.get("result", {}),
            "hard_fork": hard_fork.get("result", {}),
            "connections": connections.get("result", {}),
            "mining": mining.get("result", {}),
            "fee": fee.get("result", {})
        }
    
    def analyze_block_data(self, num_blocks=100):
        """Analyze recent blocks to extract visualization data"""
        info = self._make_rpc_call("get_info")
        if "result" not in info:
            return {"error": "Failed to get blockchain info"}
        
        height = info["result"]["height"]
        start_height = max(0, height - num_blocks)
        
        block_sizes = []
        difficulties = []
        tx_counts = []
        timestamps = []
        fees = []
        
        for h in range(start_height, height):
            block = self.get_block_by_height(h)
            if "error" in block:
                continue
            
            block_sizes.append({
                "height": h,
                "size": block.get("block_size", 0)
            })
            
            difficulties.append({
                "height": h,
                "difficulty": block.get("difficulty", 0)
            })
            
            tx_count = len(block.get("tx_hashes", []))
            tx_counts.append({
                "height": h,
                "count": tx_count
            })
            
            if "block_header" in block and "timestamp" in block["block_header"]:
                timestamps.append({
                    "height": h,
                    "timestamp": block["block_header"]["timestamp"],
                    "formatted": self._format_timestamp(block["block_header"]["timestamp"])
                })
        
        return {
            "height_range": {"start": start_height, "end": height - 1},
            "block_sizes": block_sizes,
            "difficulties": difficulties,
            "tx_counts": tx_counts,
            "timestamps": timestamps,
            "fees": fees
        }
        
    
    # API compatibility methods with new names
    
    def visualize_transaction(self, tx_hash, graph_depth=1, include_rings=True):
        """Visualize transaction with RPC data"""
        result = {
            "nodes": [],
            "links": [],
            "transaction": None,
            "error": None
        }
        
        try:
            tx_data = self.get_transaction(tx_hash)
            if "error" in tx_data:
                return {"error": tx_data["error"]}
            
            tx_node = {
                "id": tx_hash,
                "type": "transaction",
                "data": tx_data
            }
            result["nodes"].append(tx_node)
            result["transaction"] = tx_data
            
            if "tx_json" in tx_data:
                tx_json = tx_data["tx_json"]
                
                # Process inputs
                if "vin" in tx_json:
                    for idx, vin in enumerate(tx_json["vin"]):
                        if "key" in vin:
                            input_id = f"{tx_hash}_in_{idx}"
                            input_node = {
                                "id": input_id,
                                "type": "input",
                                "data": vin
                            }
                            result["nodes"].append(input_node)
                            
                            result["links"].append({
                                "source": input_id,
                                "target": tx_hash,
                                "type": "input"
                            })
                            
                            if include_rings and "key_offsets" in vin["key"]:
                                for ring_idx, offset in enumerate(vin["key"]["key_offsets"]):
                                    ring_id = f"{input_id}_ring_{ring_idx}"
                                    ring_node = {
                                        "id": ring_id,
                                        "type": "ring_member",
                                        "data": {
                                            "offset": offset,
                                            "key_image": vin["key"].get("k_image", "")
                                        }
                                    }
                                    result["nodes"].append(ring_node)
                                    
                                    result["links"].append({
                                        "source": ring_id,
                                        "target": input_id,
                                        "type": "ring_member"
                                    })
                
                # Process outputs
                if "vout" in tx_json:
                    for idx, vout in enumerate(tx_json["vout"]):
                        if "target" in vout and "key" in vout["target"]:
                            output_id = f"{tx_hash}_out_{idx}"
                            output_node = {
                                "id": output_id,
                                "type": "output",
                                "data": {
                                    "key": vout["target"]["key"],
                                    "amount": vout.get("amount", 0)
                                }
                            }
                            result["nodes"].append(output_node)
                            
                            result["links"].append({
                                "source": tx_hash,
                                "target": output_id,
                                "type": "output"
                            })
            
            # Get block info
            if "block_height" in tx_data:
                block_height = tx_data["block_height"]
                block_data = self.get_block_by_height(block_height)
                
                if "error" not in block_data:
                    block_id = str(block_height)
                    block_node = {
                        "id": block_id,
                        "type": "block",
                        "data": block_data
                    }
                    result["nodes"].append(block_node)
                    
                    result["links"].append({
                        "source": block_id,
                        "target": tx_hash,
                        "type": "contains"
                    })
            
            return result
        except Exception as e:
            return {"error": str(e)}

    def visualize_block(self, height):
        """Visualize block with RPC data"""
        result = {
            "nodes": [],
            "links": [],
            "block": None,
            "error": None
        }
        
        try:
            if isinstance(height, str):
                if height.isdigit():
                    height = int(height)
                else:
                    return {"error": "Invalid block height format"}
            
            block_data = self.get_block_with_transactions(height)
            if "error" in block_data:
                return {"error": block_data["error"]}
            
            result["block"] = block_data
            
            block_id = str(height)
            block_node = {
                "id": block_id,
                "type": "block",
                "data": block_data
            }
            result["nodes"].append(block_node)
            
            # Process miner transaction
            if "miner_transaction" in block_data:
                miner_tx = block_data["miner_transaction"]
                miner_tx_id = miner_tx.get("tx_hash", f"miner_tx_{height}")
                
                miner_tx_node = {
                    "id": miner_tx_id,
                    "type": "transaction",
                    "subtype": "miner",
                    "data": miner_tx
                }
                result["nodes"].append(miner_tx_node)
                
                result["links"].append({
                    "source": block_id,
                    "target": miner_tx_id,
                    "type": "contains",
                    "subtype": "miner"
                })
            
            # Process regular transactions
            if "transactions" in block_data:
                for tx in block_data["transactions"]:
                    tx_hash = tx.get("tx_hash", "")
                    if not tx_hash:
                        continue
                    
                    tx_node = {
                        "id": tx_hash,
                        "type": "transaction",
                        "data": tx
                    }
                    result["nodes"].append(tx_node)
                    
                    result["links"].append({
                        "source": block_id,
                        "target": tx_hash,
                        "type": "contains"
                    })
            
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_blockchain_summary(self):
        """Get blockchain summary for visualization interface"""
        info_result = self._make_rpc_call("get_info")
        if "result" not in info_result:
            return {"error": "Failed to get blockchain info"}
        
        blockchain_info = info_result["result"]
        height = blockchain_info["height"]
        
        max_blocks = 100
        blocks = []
        transactions = []
        
        start_height = max(0, height - max_blocks)
        
        for h in range(start_height, height):
            block_data = self.get_block_by_height(h)
            
            if "error" not in block_data:
                block = {
                    'height': h,
                    'hash': block_data.get("hash", ""),
                    'timestamp': block_data.get("block_header", {}).get("timestamp_formatted", "Unknown"),
                    'difficulty': block_data.get("difficulty", 0)
                }
                blocks.append(block)
                
                if "tx_hashes" in block_data:
                    for tx_hash in block_data["tx_hashes"]:
                        tx = {
                            'hash': tx_hash,
                            'block_height': h
                        }
                        transactions.append(tx)
        
        return {
            'blocks': blocks,
            'transactions': transactions
        }
        
    # For backward compatibility with existing app.py
    process_data_mdb_for_transaction = visualize_transaction
    process_data_mdb_for_block = visualize_block
    process_data_mdb_direct = get_blockchain_summary
