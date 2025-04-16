import os
import sys
from app import app
import init_db

# Set the node ID
os.environ['NODE_ID'] = 'node_1'

if __name__ == "__main__":
    print("Hospital Queue Management System - Node 1 (DEBUG MODE)")
    
    try:
        # Enable debug mode
        app.debug = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        
        print("Initializing database...")
        init_db.init_db()
        print("Database initialization complete.")
        
        print("\nAvailable routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule}")
        
        print("\nStarting application as Node 1 on port 5000...\n")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 