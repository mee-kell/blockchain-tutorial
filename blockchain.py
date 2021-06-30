import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests

class Blockchain(object):
    ''' Stores blockchain and transactions '''

    def __init__(self):

        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_nodes(self, address):
        ''' Add a new node to the list of nodes '''

        parsed_url = urlparse(address)
        
        if parsed_url.netloc:
            # Add URL of host (network location)
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without standard format
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError("Invalid URL")

    def new_block(self, proof, previous_hash=None):
        '''Creates a new block'''

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset current list of transactions
        self.current_transactions = []
        
        # Add block to chain
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        '''Adds a new transaction to the ledger'''

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        # Return index of next block which transaction is added to
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        ''' Creates a SHA-256 hash of a block '''

        # Create ordered JSON dictionary of block properties
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        ''' Returns the last block in the chain '''
        
        return self.chain[-1]

    def proof_of_work(self, last_block):
        ''' Finds a number p' such that hash(pp') contains leading 4 zeroes, 
        where p is the previous p' '''

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        ''' Verifies proof of work '''

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def valid_chain(self, chain):
        ''' Determines if a blockchain is valid by working forwards block-by-block '''

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):

            # Output information about consecutive blocks
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")

            # Check the hash of the block
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check the proof of work
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        ''' Consensus algorithm: resolves conflicts
        Replaces our chain with longest one in network '''

        neighbors = self.nodes
        new_chain = None

        # Look for chains longer than the current chain
        max_length = len(self.chain)

        # Verify all nodes in network
        for node in neighbors:

            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if chain is longer and valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        # Replace chain if a new, longer chain is discovered
        if new_chain:
            self.chain = new_chain
            return True

        return False


# Learning notes to self
#   Static method: can be called on a class without any objects
#   Property: read-only attributes
#   Proof of work: numerical solution, difficult to find but easy to verify

#   In this case, proof: find a number p that when hashed with the previous block’s 
#   solution a hash with 4 leading 0s is produced   
