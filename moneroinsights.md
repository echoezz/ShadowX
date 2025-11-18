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
- 10 blocks deep means 10 blocks before your current transaction block (Transaction Block = current Height in stagenet after issuing the status command)

### Data in a Block
- Each block in blockchain contains the info on: Timestamp, Block size, Transaction count, Miner behaviour (Miner reward, Effort, Mining trends)

** Miner reward - Reward miner receives for mining the block
** Effort - How much computational work (hashing power) the miner needed to locate the block
** Mining trends - Patterns in miner's behavior such as address reuse, hash rate changes


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

### Analysing .raw file
- Contains block in a sequential order
- Each block consists of block size field, block data (transactions, timestamp, miner reward etc.)
- It is better not to analyse the .raw file directly due to the complexity of the 

###  Decoy selection
- Decoy is choosen based on gamma distribution (the newer blocks are selected instead of older ones to simulate real-world scenario)


### About Stagnet 
Stagenet is like a Live network
Use the --offline option so your node stops talking to other stagenet peers and your height for the monero network stays fixed and doesn't syncs to the live network


