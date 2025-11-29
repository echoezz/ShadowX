import struct
import time

def parse_raw_blockchain(file_path):
    block_height = 0  # Start with the genesis block
    HEADER_BYTES = 4  # Skip the first 4 bytes (header)

    with open(file_path, "rb") as f:
        # Skip the header bytes
        f.seek(HEADER_BYTES)

        while True:
            # Read the block size (4 bytes)
            block_size_data = f.read(4)
            if not block_size_data:
                # End of file
                break
            
            # Debug: Print the raw block size bytes
            print(f"Raw block size bytes (height {block_height}): {block_size_data.hex()}")

            # Unpack the block size (little-endian unsigned int)
            try:
                block_size = struct.unpack("<I", block_size_data)[0]
            except struct.error:
                print("Error unpacking block size. Exiting.")
                break
            
            # Validate block size (sanity check)
            if block_size > 10 * 1024 * 1024:  # 10 MB limit for Monero blocks
                print(f"Invalid block size at height {block_height}: {block_size} bytes")
                break
            
            # Read the block data
            block_data = f.read(block_size)
            if len(block_data) != block_size:
                print(f"Incomplete block data at height {block_height}. Expected {block_size}, got {len(block_data)}")
                break
            
            # Parse block timestamp (example: assuming the first 4 bytes of block data is the timestamp)
            try:
                timestamp_data = block_data[:4]
                timestamp = struct.unpack("<I", timestamp_data)[0]
                readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))
            except Exception as e:
                readable_time = "Error parsing timestamp"
            
            # Print block details
            print(f"Block Height: {block_height}")
            print(f"Block Size: {block_size} bytes")
            print(f"Timestamp: {readable_time}")
            print("-" * 40)
            
            # Increment the block height
            block_height += 1

# Replace 'blockchain.raw' with the path to your .raw file
parse_raw_blockchain("/home/kali/.bitmonero/stagenet/export/blockchain.raw")
