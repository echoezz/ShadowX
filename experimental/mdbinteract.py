import lmdb
import os
import sys
import struct

# data.mdb file location supplied via args
if len(sys.argv) < 2:
    print("Usage: python mdbinteract.py /path/to/data.mdb_directory")
    sys.exit(1)

DB_PATH = sys.argv[1]

# Normalize and allow passing either the directory or the data.mdb file itself
DB_PATH = os.path.abspath(DB_PATH)
if os.path.isfile(DB_PATH) and DB_PATH.lower().endswith(".mdb"):
    # user passed the data.mdb file — use its containing directory for lmdb.open
    DB_PATH = os.path.dirname(DB_PATH)

# script to test interaction with Monero's LMDB database (data.mdb)

# test script to open and read from Monero's LMDB database
def test_lmdb_interaction(db_path):
    """
    Test script to interact with the Monero data.mdb file.
    :param db_path: Path to the Monero blockchain database (directory containing data.mdb).
    """
    # Check if the directory and data.mdb file exist
    if not os.path.exists(db_path):
        print(f"Error: Path '{db_path}' does not exist.")
        return
    if not os.path.exists(os.path.join(db_path, "data.mdb")):
        print(f"Error: No 'data.mdb' file found in '{db_path}'.")
        return

    try:
        # Open the LMDB environment (read-only)
        print(f"Opening database at '{db_path}'...")
        env = lmdb.open(db_path, readonly=True, lock=False, max_dbs=1)

        # Start a read-only transaction
        with env.begin() as txn:
            print("Database opened successfully. Attempting to read keys...")

            # Create a cursor to iterate through the database
            cursor = txn.cursor()

            # Print the first 5 keys and their sizes
            print("Reading the first 5 keys:")
            count = 0
            for key, value in cursor:
                print(f"Key: {key[:50]}... (length: {len(key)})")
                print(f"Value size: {len(value)} bytes")
                count += 1
                if count >= 5:  # Limit to 5 keys
                    break

            if count == 0:
                print("No keys found in the database. The file may be empty or corrupted.")
            else:
                print(f"Successfully read {count} keys.")

    except Exception as e:
        print(f"Error: Unable to interact with the data.mdb file. Details: {e}")
    finally:
        print("Test complete.")

# queries the 'blocks' key in the Monero LMDB database and prints the value size and a snippet of the raw binary data
def query_blocks_key(db_path):
    """
    Query and decode data from the 'blocks' key in the Monero database.
    :param db_path: Path to the Monero blockchain database (directory containing data.mdb).
    """
    # import lmdb

    # Open the database
    env = lmdb.open(db_path, readonly=True, lock=False, max_dbs=1)

    with env.begin() as txn:
        # Use a cursor to locate the 'blocks' key
        cursor = txn.cursor()
        for key, value in cursor:
            if key == b'blocks':
                print(f"Key: {key}, Value Size: {len(value)} bytes")
                print("Raw Value (first 100 bytes):", value[:100])  # Print a snippet of the raw data
                break
        else:
            print("'blocks' key not found in the database.")

# list all keys in the Monero LMDB database with their size of the corresponding values
# for exploring the structure of the monero data.mdb file
def list_all_keys(db_path):
    """
    List all keys in the Monero database.
    :param db_path: Path to the Monero blockchain database.
    """

    # import lmdb

    env = lmdb.open(db_path, readonly=True, lock=False, max_dbs=1)

    with env.begin() as txn:
        cursor = txn.cursor()
        print("Listing all keys in the database:")

        count = 0
        for key, value in cursor:
            print(f"Key: {key.decode(errors='ignore') if isinstance(key, bytes) else key}")
            print(f"Value Size: {len(value)} bytes\n")
            count += 1

        print(f"\nTotal keys displayed: {count}")

# Path to the directory containing the Monero data.mdb file
# DB_PATH = "C:/Users/YHdeo/School/DF/project/ShadowX/experimental/data.mdb"  # Replace with the actual path

def inspect_raw_values(db_path):
    """
    Inspect raw values for each key in the Monero database.
    :param db_path: Path to the Monero blockchain database.
    """
    import lmdb

    env = lmdb.open(db_path, readonly=True, lock=False, max_dbs=1)

    with env.begin() as txn:
        cursor = txn.cursor()
        print("Inspecting raw values for all keys:\n")

        for key, value in cursor:
            print(f"Key: {key.decode(errors='ignore') if isinstance(key, bytes) else key}")
            print(f"Value Size: {len(value)} bytes")
            print(f"Raw Value (Hex): {value.hex()}")  # Print raw value in hexadecimal format
            print("-" * 50)


def decode_key(hex_value, key_name):
    """
    Decode a key value dynamically based on its structure.
    :param hex_value: Raw hex value of the key.
    :param key_name: Name of the key being decoded.
    :return: Decoded fields as a dictionary.
    """
    raw_bytes = bytes.fromhex(hex_value)

    if key_name == "alt_blocks":
        # Skip decoding as it appears to be reserved/placeholder data
        return {"reserved": raw_bytes.hex()}

    elif key_name == "block_heights":
        block_hash_pointer = struct.unpack('<Q', raw_bytes[0:8])[0]
        cumulative_difficulty = struct.unpack('<Q', raw_bytes[8:16])[0]
        metadata = raw_bytes[16:].hex()
        return {
            "block_hash_pointer": block_hash_pointer,
            "cumulative_difficulty": cumulative_difficulty,
            "metadata": metadata,
        }

    elif key_name == "block_info":
        height = struct.unpack('<Q', raw_bytes[0:8])[0]
        cumulative_difficulty = struct.unpack('<Q', raw_bytes[8:16])[0]
        metadata = raw_bytes[16:].hex()
        return {
            "height": height,
            "cumulative_difficulty": cumulative_difficulty,
            "metadata": metadata,
        }

    elif key_name == "blocks":
        height = struct.unpack('<Q', raw_bytes[0:8])[0]
        timestamp = struct.unpack('<Q', raw_bytes[8:16])[0]
        metadata = raw_bytes[16:].hex()
        return {
            "height": height,
            "timestamp": timestamp,
            "metadata": metadata,
        }

    else:
        # Default: Return raw hex value
        return {"raw_value": raw_bytes.hex()}


# Example usage
example_values = {
    "alt_blocks": "00000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff",
    "block_heights": "000000001c000100000000000000000001000000000000000000000000000000a0641e0000000000a466350000000000",
    "block_info": "000000001c000100000000000000000001000000000000000000000000000000a0641e00000000006f56350000000000",
    "blocks": "000000000800040080010000000000000d500100000000006b23000000000000a0641e0000000000ca47350000000000",
}

for key_name, hex_value in example_values.items():
    decoded = decode_key(hex_value, key_name)
    print(f"Decoded Key - {key_name}: {decoded}")



if __name__ == "__main__":
    test_lmdb_interaction(DB_PATH)
    query_blocks_key(DB_PATH)
    list_all_keys(DB_PATH)  # Limit to first 50 keys for testing
    inspect_raw_values(DB_PATH)