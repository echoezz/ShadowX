import lmdb
import os

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
    import lmdb

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
def list_all_keys(db_path, limit=50):
    """
    List all keys in the Monero database.
    :param db_path: Path to the Monero blockchain database.
    :param limit: Number of keys to display (for testing purposes).
    """
    import lmdb

    env = lmdb.open(db_path, readonly=True, lock=False, max_dbs=1)

    with env.begin() as txn:
        cursor = txn.cursor()
        print("Listing all keys in the database:")
        count = 0

        for key, value in cursor:
            print(f"Key: {key}, Value Size: {len(value)} bytes")
            count += 1
            if count >= limit:
                break

        print(f"\nTotal keys displayed: {count}")

# Path to the directory containing the Monero data.mdb file
DB_PATH = "/PATH/TO/DATA.MDB FILE"  # Replace with the actual path

if __name__ == "__main__":
    test_lmdb_interaction(DB_PATH)
    query_blocks_key(DB_PATH)
    list_all_keys(DB_PATH, limit=50)  # Limit to first 50 keys for testing