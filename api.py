import sys
sys.path.append("/Users/michellelo/Desktop/Coding-Projects/Blockchain")
from blockchain import Blockchain

from flask import Flask, jsonify, request
from uuid import uuid4
import json

# Instantiate node with unique address and blockchain
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

# Mine endpoint
@app.route('/mine', methods=['GET'])
def mine():
    ''' Calculate the Proof of Work, reward the miner, and forge a new block '''

    # Run proof of work algorithm
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # The miner receives a reward from the network ("0")
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge a new block and add it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    # Notify the network
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

# Transaction endpoint
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    ''' Add a new transaction '''

    values = request.get_json()

    # Verify required fields are present
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return "Missing values", 400

    # Create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

# Blockchain endpoint
@app.route('/chain', methods=['GET'])
def full_chain():
    ''' Return the full blockchain '''

    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# Add neighboring nodes
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    ''' Add new nodes to the network '''
    
    values = request.get_json()
    nodes = values.get('nodes')

    # Check for valid list of nodes
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    # Add nodes to network one by one
    for node in nodes:
        blockchain.register_nodes(node)

    response = {
        'message': "New nodes have been added",
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

# Resolve conflicting blockchains across different nodes
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    ''' Resolve conflicting blockchains by choosing the longest valid chain'''

    # Determine and prioritise the longest valid chain
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': "Our chain was replaced",
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': "Our chain is authoritative",
            'chain': blockchain.chain
        }

    return jsonify(response), 200

# Runs server on chosen port
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='Port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)