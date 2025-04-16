import os
import sys
from app import app
import init_db

def run_node(node_id, port):
    os.environ['NODE_ID'] = node_id
    print(f"\nStarting application as {node_id} on port {port}...\n")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    print("Hospital Queue Management System")
    print("===============================\n")
    
    # Initialize the database
    print("Initializing database...")
    init_db.init_db()
    print("Database initialization complete.\n")
    
    # Node selection
    print("Select a node to run:")
    print("1. Node 1 (Port 5000)")
    print("2. Node 2 (Port 5001)")
    print("3. Node 3 (Port 5002)")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                run_node('node_1', 5000)
                break
            elif choice == "2":
                run_node('node_2', 5001)
                break
            elif choice == "3":
                run_node('node_3', 5002)
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0) 