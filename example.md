### How i simulate the example for stagenet to get the transactional details:

### First part: sending XMR
WalletA Public Address:
54F7RUVwA1TcPii6fY3W4E4JbhhC4fTriXFewW2pRxThLn89zu2pJ4rdwefkhZNpk5eKP61PSm7SKCaAZNWk5nmB3Mf5qdD

WalletB Public Address:
55UYEzi26nV1fz3LQCsQhAjEV8xvPK8QG2ruHDuHrcNTKHLqS8C1PScS8ocNCD7HAg97qMXLgotAhQYPEx4d1WEw4wXZUxP

Go Into WalletB using:
./monero-wallet-cli --stagenet
WalletB
"transfer <address> <amount>"
"transfer 54F7RUVwA1TcPii6fY3W4E4JbhhC4fTriXFewW2pRxThLn89zu2pJ4rdwefkhZNpk5eKP61PSm7SKCaAZNWk5nmB3Mf5qdD 1.0"

Output:
WalletB Transfer to WalletA 1.0 XMR

Spending from address index 0
Sending 1.000000000000.  The transaction fee is 0.000061410000

Transaction successfully submitted, transaction <f80e7aff7adf7158eecdabdee772151ce4f08373ccfa9c5c27e6dd5fe73fcdad>
You can check its status by using the `show\_transfers` command.

Note:
Because there will be a new transaction into the blockchain network, it becomes out of sync after transferring.

After awhile the output from WalletB:

Height 1990415, txid <f80e7aff7adf7158eecdabdee772151ce4f08373ccfa9c5c27e6dd5fe73fcdad>, 1.280612285469, idx 0/0
Height 1990415, txid <f80e7aff7adf7158eecdabdee772151ce4f08373ccfa9c5c27e6dd5fe73fcdad>, spent 0.817171042774, idx 0/0
Height 1990415, txid <f80e7aff7adf7158eecdabdee772151ce4f08373ccfa9c5c27e6dd5fe73fcdad>, spent 1.463502652695, idx 0/0
Refresh done, blocks received: 2
Currently selected account: [0] Primary account
Tag: (No tag assigned)
Balance: 7.368195763585, unlocked balance: 6.087583478116 (8 block(s) to unlock)

### Installing vscode
Download from: https://code.visualstudio.com/docs/setup/linux#_install-vs-code-on-linux
sudo apt install ./xxxx.deb

### Second part: Getting the details

Normally work off the inner transaction JSON (the as_json part), not the whole RPC wrapper. inner transaction JSON contains:
version, unlock_time,vin, vout, extra, rct_signatures.

That's why choose the .txs[0].as_json
Query the transaction:

curl -X POST http://127.0.0.1:38081/get_transactions \
  -H 'Content-Type: application/json' \
  -d '{"txs_hashes":["f80e7aff7adf7158eecdabdee772151ce4f08373ccfa9c5c27e6dd5fe73fcdad"], "decode_as_json": true}' \
  | jq -r '.txs[0].as_json'

.txs[0].as_json - Extracts the as_json string of the first transaction and prints it as a real multi-line block instead of one long escaped string
jq - makes the JSON pretty print


Contains all the transaction input information:

vin[0] - input 0
vin[1] - input 1

The different fields in vin:

amount: usually 0 for RingCT bec the amts are hidden - need the private view key to see
k_image: the key image (unique value derived from the real output being spent and the spender's secret key)
You cannot reverse a key image to see which ring member was real

vin basically tells you “this tx is (anonymously) spending some outputs with these global indices, and here’s the key image proving one of them is real.”
key_offsets: Array of relative offsets that point to the ring members (decoy outputs+real one)


vout contains all the transaction output information
Each element = one output of the transaction

Different fields:
target.key = one-time public key that only the recipient can recognize and spend. On-chain, you can never see the recipient's wallet address; you see these one-time keys instead.

To get the indexes below:
Get the key_offsets value from the txs.as_json 
Once gathered
Starting from index 0, which should remain the same.
index 1 value is index0 + the value in index1
index 2 value is index1 (The new value) + the value in index2
index 3 value is index2 (The new value) + the value in index2
.......
index 15 value is index14 (The new value) + the value in index15

curl -s -X POST http://127.0.0.1:38081/get_outs \
  -H "Content-Type: application/json" \
  --data '{
    "outputs": [
      {"amount": 0, "index": 9626785},
      {"amount": 0, "index": 9631953},
      {"amount": 0, "index": 9633587},
      {"amount": 0, "index": 9634135},
      {"amount": 0, "index": 9634431},
      {"amount": 0, "index": 9634798},
      {"amount": 0, "index": 9635114},
      {"amount": 0, "index": 9635151},
      {"amount": 0, "index": 9635383},
      {"amount": 0, "index": 9635397},
      {"amount": 0, "index": 9635403},
      {"amount": 0, "index": 9635404},
      {"amount": 0, "index": 9635525},
      {"amount": 0, "index": 9635557},
      {"amount": 0, "index": 9635693},
      {"amount": 0, "index": 9635722}
    ],
    "get_txid": true
  }' | jq

You should get a list of outputs like this shown below:

{
  "credits": 0,
  "outs": [


    {
      "height": 1986905,
      "key": "341aefaae9f4c0764c3e54f0a8b90559351719fb03a29100d514e4848a86db45",
      "mask": "a8709ba0e48fd0ecfd3ecdac6afd4e5859b0726f9d2aba496fff49004ba38391",
      "txid": "5a299299c415eb0e53679e4b84aba21d1caca6f2f7de3c9b48b3b028b0d27219",
      "unlocked": true
    },
    {
      "height": 1988385,
      "key": "b1a742856d738043b27ab5e85d70d444f28de3757aec8763dd52d0c32a6f4492",
      "mask": "6873ae7722c789f67d4de898fc717e428024866a94a2c00a9657456c333336fd",
      "txid": "42ff776d2c7692acc99482e7cf0cbf61b6befc3015d244407339c64041f375ae",
      "unlocked": true
    },
    {
      "height": 1988895,
      "key": "a9085bec0c02279058426434655521163664df10c807f3ad4f9f6ad8d7a78218",
      "mask": "59dfab755143fdc36fee369d5b001075874f8690814ec44d9552532819c7a314",
      "txid": "bb7c0a58191fb47623fb4a38c9652607abbb9130ab108fb7b052d935369c8520",
      "unlocked": true
    },
    {
      "height": 1989135,
      "key": "47711a5ad560d3d42a0609c029beb02c2339baa68c13967ee1242253012383be",
      "mask": "0cb470c613a5874ffc348bbbe3aad0a5c08446ca0d408b71ef9f89197f590219",
      "txid": "6eb96904e138f502009ec9ce81eae47d40da5629c001f97e71c8e938de197d2d",
      "unlocked": true
    },
    {
      "height": 1989482,
      "key": "da4214035480b5ed0a1c7891e10eacaf5a39303ee16ad38030e2e769a1d41bc4",
      "mask": "30e69173e5dbf0215cef72fb73fc8346508a3ea189fa5d0958f664c8aeeda2de",
      "txid": "6e8f9a5729daca1a5c3c6d05f2777586f76070179518ff1065375d471c5baa11",
      "unlocked": true
    },
    {
      "height": 1989778,
      "key": "298af089e369a6044aeed23c0a222587e39ac83b225e25c4e8c80f0624e55a9c",
      "mask": "178aa14afe78b0be266e048c5adac316058fb5863aa87c555477d0bd714bb713",
      "txid": "7cc71977676ecf50a203ee089e0daf515d30d0d46de6e276117db5a00d01aa7a",
      "unlocked": true
    },
    {
      "height": 1989813,
      "key": "930ccf91975cd5c366a36dd5b5a13eaa5055b614aa045415b01d69c2ddb50e6d",
      "mask": "d73654f25b810f468487f7bedd28aaca3fd2178826ffca9556680e0d034c6909",
      "txid": "599884aec88eff971ba676daa9f2ca3f1a8535ba7a905df99f148e8e2aa83f2c",
      "unlocked": true
    },
    {
      "height": 1990035,
      "key": "6a1ecc65d72ed04909fcef4c197bea7cd0085211f83e85570f58fa460efdba9c",
      "mask": "96ea3d18b03f35eabd61eea6493dcb0663a03c571dd0293770460ca2956a0886",
      "txid": "32e313e9718aa7f9fc7ff6efba7a1794bf2b6acae0bcc084c5cbd3aedff69a2c",
      "unlocked": true
    },
    {
      "height": 1990047,
      "key": "1c3631cf2aca2f31392d057f9e30ffbb27efcc9f453b841335cf74dc6e7cdd95",
      "mask": "994f6bf0689295808ba619f40ddc1b563d7f5ea38c430afb2295c38456cab1e0",
      "txid": "2b383df2583d75ce619180fb5d913303e01077376c36688b8c1cabf982c0b3f5",
      "unlocked": true
    },
    {
      "height": 1990053,
      "key": "b7eb0c1b6269bf1b5aead751831b83c959ee25314010020c5573c40aee7fe3d8",
      "mask": "9f233e4be87c118cc6e7bbba62083bd5312772534d3e3483ffdf3af78fcdc90a",
      "txid": "aaa6e41c2ceccc11cfd13aa2e518f6d4b42384b0dacbe3fbeac6df5a83440af6",
      "unlocked": true
    },
    {
      "height": 1990054,
      "key": "1e62c01a6625adfc4029dd401e15e8061f960962b6d609b89178879b9f5c6020",
      "mask": "05314c06a026caf74d1992c8d6a2831bb37f0c5c39639949d66e75d79539b486",
      "txid": "44b99c53a1ab7e0d0f54caa4f74abc420748942b627479a94e08f9d5e1d99db7",
      "unlocked": true
    },
    {
      "height": 1990169,
      "key": "da0ee85c068c3e3659dc6fabb75d8f6534596e5c1fb1f1a687a0954a6dd396b1",
      "mask": "ed51a40335ea03bf0c42e8f5cc2925e808b3684a52d65d255c3cafb37d9c06e7",
      "txid": "d8e4b929c0481d163e5121b133fb2c2d9ed3c032ab0a36c658bdee6b6c0a62f2",
      "unlocked": true
    },
    {
      "height": 1990193,
      "key": "489151f7a39e18252c744d169670c7a8fc5a9c7c1e954e5e346ff80325507619",
      "mask": "2832f2e1fd7a938fb063d246e0c032bd29a0b47ba43067134e346a98fef8bdbb",
      "txid": "56aac0605db0e9e595911ce1c27a6482e67eb5db55e5a40ef0a24d0cc7f2fd75",
      "unlocked": true
    },
    {
      "height": 1990307,
      "key": "03de346be485506352794cffc4590b37d2c4de1f9382221d3f7a7ed73cd07f3b",
      "mask": "7c53510dd25230a20f6f931e5d2468965d3df659da36da252db4f7ec8c4b80d6",
      "txid": "641dbac7d29a67ed9f41c93193e87da33aef4ade9531f07e15a548435a1471dc",
      "unlocked": true
    },
    {
      "height": 1990330,
      "key": "0fb677098ecad1e563caa06f9d8082185d33f9e8e678c65d301494b2a2fcbcb1",
      "mask": "111fc9388352c8e1b2d0093cef54f4371804aac51dd15f50ddb6efcf610e9168",
      "txid": "8d3e36b1edb5e46a3375bc06ebe2e65c9304d4798425a7dccb3e5977865374d1",
      "unlocked": true
    }
  ],
  "status": "OK",
  "top_hash": "",
  "untrusted": false
}

### Each element of outs corresponds to one ring member of that input.

To verify that the mapping is correct:
Replace the txs_Hash with the txid and make sure that the key field value matches in the vout.


curl -X POST http://127.0.0.1:38081/get_transactions \\n  -H 'Content-Type: application/json' \\n  -d '{"txs_hashes":["8d3e36b1edb5e46a3375bc06ebe2e65c9304d4798425a7dccb3e5977865374d1"], "decode_as_json": true}' | jq -r '.txs[0].as_json'


To get the spending height:

curl -X POST http://127.0.0.1:38081/get_transactions \
  -H 'Content-Type: application/json' \
  -d '{
    "txs_hashes": ["f80e7aff7adf7158eecdabdee772151ce4f08373ccfa9c5c27e6dd5fe73fcdad"],
    "decode_as_json": true
  }' | jq | grep 'height'



Next step: 

- Age / temporal heuristics,
- Transaction-graph building,
- Any probabilistic “real vs decoy” analysis.
- Automate the script 

Age-Based Heuristic (Probabilistic):

Compute Age in Blocks:
age_blocks = spend_height - origin_height

Convert Blocks to Days (Since 1 block is 120 seconds):
age_days = age_blocks / 720 



