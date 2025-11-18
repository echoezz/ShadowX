## How monero provides privacy

- ringCT - hide the transactional amt

- stealth add - random one time address used for every transaction 

- ring signature - makes use of our acct key and a no. of public keys pulled from blockchain (hiding the possibility of discovering the signer for our acct, hence keeping transaction outputs untraceable)


## Understanding monero

### BlockHeight
- Sequential no. of a block within blockchain, starting from very first block (aka Genesis block with the Height=0). Next block will be 1 and so on.
- TLDR, it is the position of a block in the blockchain
- In Monero, a new block gets added every 2 min.
(A block consists of info: Unqiue block hash, a list of transactions, metadata(timestamp, miner reward, size))
- Blockheight will help to identify specific blocks, tracks blockchain growth, synchronizes nodes and determine the transaction confirmation
** No. of Transaction Confirmation = The difference between current block height and block height of the block containing our transaction


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


### Analysing .raw file
- Contains block in a sequential order
- Each block consists of block size field, block data (transactions, timestamp, miner reward etc.)
- It is better not to analyse the .raw file directly due to the complexity of the


### Block analysis
- Inspecting blocks (individual unit tht make up the blockchain)
- understanding the transaction contained in those blocks
- analyzing network level patterns (?)


# About data.mdb
- It is a binary database managed by LMDB (Lightning Memory-Mapped Database), which stores Monero's blockchain data in a highly optimized, but non-human-readable format.
- data.mdb uses the LMDB database engine, which stores key-value pairs. Keys and values are stored as binary objects, not plain text.
- The blockchain data (such as blocks, transaction) is stored in serialized C++ structures unique to monero. To decode it requires understanding of Monero internal serialization format, which is implemented in Monero Source Code (C++)
- Currently there isnt a way to parse data.mdb, as such most make use of RPC API calls to interact the blockchain data as it includes the decoding logic already
- The data.mdb contains several tables (or maps) to store diff. parts of the blockchain. (Can refer to monero source code to find out)