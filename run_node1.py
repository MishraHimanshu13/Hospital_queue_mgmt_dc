import os
from app import app
import init_db

# Set the node ID
os.environ['NODE_ID'] = 'node_1'

if __name__ == "__main__":
    print("Hospital Queue Management System - Node 1")
    print("Initializing database...")
    init_db.init_db()
    print("\nStarting application as Node 1 on port 5000...\n")
    app.run(host='0.0.0.0', port=5000, debug=True) 