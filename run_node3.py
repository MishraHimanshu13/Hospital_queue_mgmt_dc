import os
from app import app

# Set the node ID
os.environ['NODE_ID'] = 'node_3'

if __name__ == "__main__":
    print("Hospital Queue Management System - Node 3")
    print("\nStarting application as Node 3 on port 5002...\n")
    app.run(host='0.0.0.0', port=5002, debug=True) 