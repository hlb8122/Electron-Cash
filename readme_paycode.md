Proof of concept of "reusable addresses proposal. https://github.com/imaginaryusername/Reusable_specs/blob/master/reusable_addresses.md

This is a CLI implementation in Electron Cash that has 3 functions:

1. generate_paycode()

This will generate a new paycode, using your wallet's receiving address 0 pubkey as the scanpubkey and receiving address 1 as the spendpubkey.  The checksum is not operable.  

2. pay_to_paycode()

This creates a raw transaction.  You need to specify both the address and the outpoint, plus the transaction amount.  WARNING: the amount to send is in full bitcoins.  

Usage:  (example for 0.1 BCH):

pay_to_paycode(0.1,0,"1NJxyu.......","0e38.....38882fb:21","paycode")

3. receive_paycode_transaction()

This takes a transaction and unpacks it using the paycode to generate the address.  The output is the private key.  It does not validate to see if the paycode matches.

This does not implement libsec256k1 as it was faster and clearer to use pure python.
