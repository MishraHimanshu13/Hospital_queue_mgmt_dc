import os
from app import app

# Set the node ID
os.environ['NODE_ID'] = 'node_2'

if __name__ == "__main__":
    print("Hospital Queue Management System - Node 2")
    print("\nStarting application as Node 2 on port 5001...\n")
    app.run(host='0.0.0.0', port=5001, debug=True) 