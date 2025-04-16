from app import app, db, User
import os

def init_db():
    """Initialize the database with schema and default users."""
    # Create tables
    with app.app_context():
        # For SQLite file path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path and '/' in db_path:  # Only create directories for paths with directories
            dir_path = os.path.dirname(db_path)
            if dir_path:  # Only create if there's a directory component
                os.makedirs(dir_path, exist_ok=True)
        
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin user already exists
        if User.query.filter_by(username='admin').first() is None:
            print("Adding default users...")
            # Create default admin
            admin = User(username='admin', name='Administrator', role='admin', active=True)
            admin.set_password('admin123')
            
            # Create default receptionist
            receptionist = User(username='reception', name='Receptionist Staff', role='receptionist', node_id='node_1', active=True)
            receptionist.set_password('reception123')
            
            # Create default doctor
            doctor = User(username='doctor', name='Doctor Staff', role='doctor', active=True)
            doctor.set_password('doctor123')
            
            # Create default pharmacist
            pharmacist = User(username='pharmacy', name='Pharmacy Staff', role='pharmacist', active=True)
            pharmacist.set_password('pharmacy123')
            
            # Add users to database
            db.session.add_all([admin, receptionist, doctor, pharmacist])
            db.session.commit()
            print("Default users added successfully.")
        else:
            print("Default users already exist. Skipping user creation.")

if __name__ == "__main__":
    init_db()
    print("Database initialization complete.") 