# Understanding monero

### How monero provides privacy

- ringCT - hide the transactional amt

- stealth add - random one time address used for every transaction 

- ring signature - makes use of our acct key and a no. of public keys pulled from blockchain (hiding the possibility of discovering the signer for our acct, hence keeping transaction outputs untraceable)

### Analysing .raw file
- Contains block in a sequential order
- Each block consists of block size field, block data (transactions, timestamp, miner reward etc.)
- It is better not to analyse the .raw file directly due to the complexity of the decoding to human-readable

### About data.mdb
- It is a binary database managed by LMDB (Lightning Memory-Mapped Database), which stores Monero's blockchain data in a highly optimized, but non-human-readable format.
- data.mdb uses the LMDB database engine, which stores key-value pairs. Keys and values are stored as binary objects, not plain text.
- The blockchain data (such as blocks, transaction) is stored in serialized C++ structures unique to monero. To decode it requires understanding of Monero internal serialization format, which is implemented in Monero Source Code (C++)
- Currently there isnt a way to parse data.mdb, as such most make use of RPC API calls to interact the blockchain data as it includes the decoding logic already
- The data.mdb contains several tables (or maps) to store diff. parts of the blockchain. (Can refer to monero source code to find out)
- lock.mdb is required for monero stagenet to reference to a data.mdb. If lock.mdb is not found, monero will recreate a stagenet folder each time. (It is also okay to generate a lock.mdb - does not require user to upload one to the webapp)

### BlockHeight
- Sequential no. of a block within blockchain, starting from very first block (aka Genesis block with the Height=0). Next block will be 1 and so on.
- TLDR, it is the position of a block in the blockchain
- In Monero, a new block gets added every 2 min.
(A block consists of info: Unqiue block hash, a list of transactions, metadata(timestamp, miner reward, size))
- Blockheight will help to identify specific blocks, tracks blockchain growth, synchronizes nodes and determine the transaction confirmation
** No. of Transaction Confirmation = The difference between current block height and block height of the block containing our transaction
- 10 blocks deep means 10 blocks before your current transaction block (Transaction Block = current Height in stagenet after issuing the status command)

### Data in a Block
Each block in blockchain contains the info on: 
1. Block Height -> Indicates the sequential order of the block in the chain
2. Block Hash -> Used to verify the integrity of a block. Any change to the block's data would result in a different hash, making tampering detectable.
3. Previous block hash -> Links the current block to the previous one, forming the chain structure of the blockchain.
4. Timestamp -> Allows for chronological ordering of blocks and provides a record of when the block was added to the chain.
5. Nonce -> Miners adjust the nonce to find a hash that meets the blockchain's difficulty target.
6. Difficulty -> Ensures that blocks are mined at a consistent rate by adjusting the difficulty based on the network's hash rate.
7. Transaction merkle root -> Allows for efficient verification of transactions within the block without needing to download the entire block.
8. Major/Minor Version -> Tracks upgrades or changes to the blockchain’s protocol.
Major: Indicates significant protocol changes (e.g., hard forks).
Minor:Indicates smaller updates or backward-compatible changes.
9. Miner reward -> Incentivizes miners to secure the network and validate transactions.
10. Cumulative difficulty -> Provides a measure of the total computational work done to secure the blockchain.


### Miner reward
- newly created coins that are being paid to the miner for adding a valid block to the chain
- nobody send you that coin
- block unlocked is like a reward for mining that block 

### Step by step what actually happens in a block
- Many users broadcast transactions (A to B, B to C, etc)
- Miners would then collect the transactions into a candidate block
- Each miner adds one special transaction at the top of the block:
    - Coinbase transaction
    - "Create up to X new XMR + collect all transaction fees and then send them to address X (the miner's address)
- Miner runs Proof-Of-Work until the block hash satisfies the difficulty
- If the block is valid and other nodes accept it:
    - Everyone agrees that this special transaction is valid
    - The coins it created now exist and belong to the miner

### More about the transactions
- User initate transactions (walletA --> walletB). Transaction broadcast to monero network and received by nodes (Nodes are the computers running the monero software). Nodes validate the transaction and add it to mempool (unconfirmed transaction waiting area)
- Miners take unconfirmed transactions from the mempool and package them into a new block. (A block contains a list of transactions across the monero network and also a coinbase transaction - which is a special transction that rewards miners with newly created XMR and transaction fees from the included transactions)
- Miners solves a cryptographic puzzle. Once they solve it, the new block is then broadcast to the network. Other nodes will also validate to ensure it is valid. If valid, block is added to blockchain
** Take note, Miners do not add transactions directly to blockchain, they packaged transactions into a new block, where once it is added to blockchain, it includes both miner's reward and transactions


### Decoy selection
- Decoy is choosen based on gamma distribution (the newer blocks are selected instead of older ones to simulate real-world scenario)


### About Stagnet 
Stagenet is like a Live network
Use the --offline option so your node stops talking to other stagenet peers and your height for the monero network stays fixed and doesn't syncs to the live network


### Block analysis
- Inspecting blocks (individual unit tht make up the blockchain)
- understanding the transaction contained in those blocks
- analyzing network level patterns (?)


### Wallet Details 

- Private view key (Derived from seed/private spend key (b = H(a)))
    - Required to view all the transactions regarding the account
    - Steps:
        - Scans every transaction on-chain
        - Decrypt/recognise outputs sent to you (recipient's one-time addresses)
        - it sees all your incoming inputs
        - Any change outputs that come back to you

    But the view key has no way to know which of your previous outputs have later been spent, because in Monero:

    Inputs are hidden inside ring signatures with decoys. (?)

    The “real spent output” is not explicitly marked on-chain. (?)

    The link between “this key image” and “that owned output” requires the private spend key. (?)

    - In this sense, it can only see this output belongs to you but you wouldn't know whether it is spend.

    - Every Monero address has a private viewkey which can be shared. In this case, enabling someone to see all the incoming transactions for that address.
    - As of June 2017, outgoing transactions cannot be accurately seen. Hence, the balance of a Monero address via a viewkey should not be relied upon 


- Private spend key (Derived from seed)
    - Required to accurately know which is the output that is spent and the balance left on the wallet
    - Utilized to generate key image for your outputs (?)
    - Can be utilized to generate private viewkey
    - Utilized to spend any funds in the account
    - 256-bit integer used to sign Monero Transactions
    - With this it can reconstruct the private


- Key image is unique; that specific output cannot be spent twice (?)
- Cannot tell which member of the ring is real (?)
- To Compute key image for an owned output, need the private spend key (?)

(No references yet:)
With the private spend key:
You can generate the same key images for all your owned outputs, and match them to key images on-chain → you know exactly which outputs are spent → you know outgoing transactions and correct balance.

With only the private view key:
You cannot generate key images, so you cannot check which of your outputs were spent. You might guess from changes in balance or seeing change outputs, but this is not cryptographically reliable.

That is why the docs say “outgoing transactions cannot be reliably viewed” with just a view key.


Sources:
https://web.getmonero.org/resources/moneropedia/viewkey.html
https://www.getmonero.org/resources/user-guides/view_only.html


https://www.getmonero.org/resources/moneropedia/spendkey.html


