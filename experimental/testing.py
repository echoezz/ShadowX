import lmdb

# call the lmdb file
lmdb_path = 'path/to/your/lmdb/file'

# open the lmdb environment
lmdb_env = lmdb.open(lmdb_path, readonly=True, max_dbs=10)

# open blocks & transactions db
block_db = lmdb_env.open_db(b'blocks')
tx_db = lmdb_env.open_db(b'txs')

print("LMDB database loaded successfully!")

def get_total_transactions(env, tx_db):
    """Counts the total number of transactions in the Monero LMDB database."""
    with env.begin(db=tx_db) as txn:
        count = 0
        cursor = txn.cursor()  # Cursor to iterate through the database
        for _ in cursor:
            count += 1
    return count

def get_total_blocks(env, block_db):
    with env.begin(db=block_db) as txn:
        count = 0
        cursor = txn.cursor()
        for _ in cursor:
            count += 1
    return count

total_blocks = get_total_blocks(lmdb_env, block_db)
print(f"Total Number of Blocks: {total_blocks}")

tx_db = lmdb_env.open_db(b'txs')  # Open the 'txs' database

# Get the total number of transactions
total_transactions = get_total_transactions(lmdb_env, tx_db)
print(f"Total Number of Transactions: {total_transactions}")