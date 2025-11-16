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
- Each block in blockchain contains the info on: Timestamp, Block size, Transaction count, Miner behaviour (Miner reward, Effort, Mining trends)

** Miner reward - Reward miner receives for mining the block
** Effort - How much computational work (hashing power) the miner needed to locate the block
** Mining trends - Patterns in miner's behavior such as address reuse, hash rate changes

### Analysing .raw file
- Contains block in a sequential order
- Each block consists of block size field, block data (transactions, timestamp, miner reward etc.)
- It is better not to analyse the .raw file directly due to the complexity of the


### Block analysis
