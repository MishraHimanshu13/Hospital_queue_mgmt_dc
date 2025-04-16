from flask import Flask, render_template, request, jsonify, Response, stream_with_context, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import time
import json
import random
import threading
import os
from datetime import datetime
import logging
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_queue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True  # Enable debug mode

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Global variables for Ricart-Agrawala algorithm
node_id = os.environ.get('NODE_ID', 'node_1')  # Default node ID
logical_clock = 0
request_queue = []
replied_nodes = set()
state = "RELEASED"  # RELEASED, WANTED, HELD
mutex = threading.Lock()
deferred_replies = []

# Database models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # receptionist, doctor, pharmacist, admin
    node_id = db.Column(db.String(10), nullable=True)  # For receptionists
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    unique_4digit = db.Column(db.String(4), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='Waiting for Doctor')  # Waiting for Doctor, In Consultation, Ready for Pharmacy, Checked Out
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    queue_position = db.Column(db.Integer, default=0)
    
    # Relationships
    assigned_doctor = db.relationship('User', backref='patients')
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medicine = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MutexLog(db.Model):
    __tablename__ = 'mutex_logs'
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(10), nullable=False)
    event = db.Column(db.String(20), nullable=False)  # REQUEST, REPLY, CRITICAL_SECTION, etc.
    timestamp = db.Column(db.Integer, nullable=False)  # Lamport logical timestamp
    target_node = db.Column(db.String(10), nullable=True)  # Target node for REQUEST/REPLY
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ricart-Agrawala algorithm functions
def log_mutex_event(event_type, target_node=None):
    """Helper function to log mutex events with proper timestamps"""
    global logical_clock
    with mutex:
        try:
            logical_clock += 1
            log_entry = MutexLog(
                node_id=node_id,
                event=event_type,
                timestamp=logical_clock,
                target_node=target_node,
                created_at=datetime.utcnow()  # Use UTC time for consistency
            )
            db.session.add(log_entry)
            db.session.commit()
            logger.info(f"Mutex event logged: {event_type} from {node_id} to {target_node} at {log_entry.created_at}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to log mutex event: {str(e)}")
            raise  # Re-raise the exception to handle it in the calling function

def request_critical_section():
    """Request access to critical section"""
    global state, logical_clock, replied_nodes
    with mutex:
        state = "WANTED"
        logical_clock += 1
        request_timestamp = logical_clock
        
        # Log the request event
        log_mutex_event("REQUEST")
        
        # In single-node mode, we automatically grant access to critical section
        state = "HELD"
        log_mutex_event("CRITICAL_SECTION")
        
        return True

def release_critical_section():
    """Release critical section"""
    global state, deferred_replies
    with mutex:
        state = "RELEASED"
        log_mutex_event("RELEASE")
        
        # Process and log deferred replies
        for deferred_node in deferred_replies:
            log_mutex_event("REPLY", deferred_node)
        
        deferred_replies = []

def handle_request(request_node, request_timestamp):
    """Handle incoming request for critical section"""
    global state, logical_clock
    with mutex:
        logical_clock = max(logical_clock, request_timestamp) + 1
        
        if state == "HELD" or (state == "WANTED" and (logical_clock, node_id) < (request_timestamp, request_node)):
            deferred_replies.append(request_node)
            log_mutex_event("DEFER", request_node)
            return False
        else:
            log_mutex_event("REPLY", request_node)
            return True

def handle_reply(reply_node):
    """Handle reply from other node"""
    global replied_nodes
    with mutex:
        replied_nodes.add(reply_node)
        log_mutex_event("RECEIVED_REPLY", reply_node)

# Helper function to get the next queue position for a doctor
def get_next_queue_position(doctor_id):
    # Find the highest queue number for this doctor and add 1
    highest_queue = db.session.query(func.max(Patient.queue_position))\
        .filter(Patient.assigned_doctor_id == doctor_id, Patient.status == "Waiting for Doctor").scalar()
    
    # If no patients in queue, start at 1
    if highest_queue is None:
        return 1
    return highest_queue + 1

# Routes
@app.route('/')
def index():
    return render_template('patient.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.active:
            login_user(user)
            
            # Map roles to correct route paths
            role_routes = {
                'admin': '/admin',
                'doctor': '/doctor',
                'receptionist': '/receptionist',
                'pharmacist': '/pharmacy'  # This maps the 'pharmacist' role to the '/pharmacy' route
            }
            
            # Get the correct route or default to role name
            redirect_path = role_routes.get(user.role, f'/{user.role}')
            
            return jsonify({
                "success": True, 
                "role": user.role, 
                "redirect": redirect_path
            })
        
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"success": True})

@app.route('/patient')
def patient_portal():
    return render_template('patient.html')

@app.route('/receptionist')
@login_required
def receptionist_portal():
    if current_user.role != 'receptionist':
        return redirect(url_for('login'))
    return render_template('receptionist.html')

@app.route('/doctor')
@login_required
def doctor_portal():
    if current_user.role != 'doctor':
        return redirect(url_for('login'))
    return render_template('doctor.html')

@app.route('/pharmacy')
@login_required
def pharmacy_portal():
    if current_user.role != 'pharmacist':
        return redirect(url_for('login'))
    return render_template('pharmacy.html')

@app.route('/admin')
@login_required
def admin_portal():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html')

# Patient routes
@app.route('/patient/status/<unique_id>')
def patient_status(unique_id):
    patient = Patient.query.filter_by(unique_4digit=unique_id).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Calculate estimated wait time based on queue position
    estimated_wait_time = patient.queue_position * 5  # Assuming 5 minutes per patient
    
    prescriptions = [p.medicine for p in patient.prescriptions]
    
    return jsonify({
        "patientName": patient.name,
        "stage": patient.status,
        "queuePosition": patient.queue_position,
        "totalInQueue": Patient.query.filter_by(
            assigned_doctor_id=patient.assigned_doctor_id,
            status="Waiting for Doctor"
        ).count(),
        "estimatedWaitTime": estimated_wait_time,
        "assignedDoctor": patient.assigned_doctor.name if patient.assigned_doctor else None,
        "prescriptions": prescriptions
    })

@app.route('/patient/events/<unique_id>')
def patient_events(unique_id):
    def generate():
        patient = Patient.query.filter_by(unique_4digit=unique_id).first()
        if not patient:
            yield f"data: {json.dumps({'error': 'Patient not found'})}\n\n"
            return
        
        last_status = None
        while True:
            patient = Patient.query.filter_by(unique_4digit=unique_id).first()
            if not patient:
                yield f"data: {json.dumps({'error': 'Patient not found'})}\n\n"
                break
            
            # Only send update if status changed
            if patient.status != last_status:
                estimated_wait_time = patient.queue_position * 5
                prescriptions = [p.medicine for p in patient.prescriptions]
                
                data = {
                    "patientName": patient.name,
                    "stage": patient.status,
                    "queuePosition": patient.queue_position,
                    "totalInQueue": Patient.query.filter_by(
                        assigned_doctor_id=patient.assigned_doctor_id,
                        status="Waiting for Doctor"
                    ).count(),
                    "estimatedWaitTime": estimated_wait_time,
                    "assignedDoctor": patient.assigned_doctor.name if patient.assigned_doctor else None,
                    "prescriptions": prescriptions
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                last_status = patient.status
            
            time.sleep(2)  # Check for updates every 2 seconds
    
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

# Receptionist routes
@app.route('/api/receptionist/register', methods=['POST'])
def register_patient():
    # Check if user is authenticated before checking role
    if not current_user.is_authenticated:
        logger.error("Unauthenticated access attempt to register patient")
        return jsonify({"success": False, "error": "Please log in first"}), 401
        
    # Check if user has the correct role
    if current_user.role != 'receptionist':
        logger.error(f"Unauthorized access attempt by {current_user.username} with role {current_user.role}")
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        logger.info(f"Received registration request: {data}")
        patient_name = data.get('name')
        patient_contact = data.get('contact')
        doctor_id = data.get('doctorId')
        
        if not patient_name or not doctor_id:
            logger.error(f"Missing required fields: name={patient_name}, doctor_id={doctor_id}")
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        logger.info("Generating unique 4-digit ID...")
        # Generate unique 4-digit ID directly
        while True:
            unique_id = str(random.randint(1000, 9999))
            existing_patient = Patient.query.filter_by(unique_4digit=unique_id).first()
            if not existing_patient:
                logger.info(f"Generated unique ID: {unique_id}")
                break
        
        # Calculate queue position
        queue_position = Patient.query.filter_by(
            assigned_doctor_id=doctor_id,
            status="Waiting for Doctor"
        ).count() + 1
        logger.info(f"Queue position: {queue_position}")
        
        # Create new patient
        new_patient = Patient(
            unique_4digit=unique_id,
            name=patient_name,
            contact=patient_contact,
            assigned_doctor_id=doctor_id,
            queue_position=queue_position
        )
        
        logger.info("Adding patient to database...")
        db.session.add(new_patient)
        db.session.commit()
        logger.info(f"Patient {patient_name} registered successfully with ID {unique_id}")
        
        # Log the action
        log_entry = MutexLog(
            node_id=node_id,
            event="PATIENT_REGISTERED",
            timestamp=logical_clock,
            target_node=None
        )
        db.session.add(log_entry)
        db.session.commit()
        logger.info("Mutex log entry created")
        
        doctor = User.query.get(doctor_id)
        
        return jsonify({
            "success": True,
            "patientId": unique_id,
            "doctorName": doctor.name if doctor else "Unknown"
        })
    
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        logger.error(f"Error registering patient: {error_message}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": error_message}), 500

@app.route('/api/receptionist/doctors')
@login_required
def get_doctors():
    if current_user.role != 'receptionist':
        return jsonify({"error": "Unauthorized"}), 403
    
    doctors = User.query.filter_by(role='doctor', active=True).all()
    doctor_list = []
    
    for doctor in doctors:
        queue_length = Patient.query.filter_by(
            assigned_doctor_id=doctor.id,
            status="Waiting for Doctor"
        ).count()
        
        doctor_list.append({
            "id": doctor.id,
            "name": doctor.name,
            "queueLength": queue_length,
            "specialty": "General Medicine"  # This would come from an additional field in the User model
        })
    
    return jsonify(doctor_list)

@app.route('/api/receptionist/waiting-patients')
@login_required
def get_waiting_patients():
    if current_user.role != 'receptionist':
        return jsonify({"error": "Unauthorized"}), 403
    
    patients = Patient.query.filter(
        Patient.status.in_(["Waiting for Doctor", "In Consultation"])
    ).order_by(Patient.registration_time).all()
    
    patient_list = []
    for patient in patients:
        estimated_wait_time = patient.queue_position * 5
        
        patient_list.append({
            "id": patient.unique_4digit,
            "name": patient.name,
            "assignedDoctor": patient.assigned_doctor.name if patient.assigned_doctor else "Unassigned",
            "queuePosition": patient.queue_position,
            "estimatedWaitTime": estimated_wait_time,
            "status": patient.status
        })
    
    return jsonify(patient_list)

@app.route('/api/receptionist/waiting-patients/events')
@login_required
def waiting_patients_events():
    if current_user.role != 'receptionist':
        return jsonify({"error": "Unauthorized"}), 403
    
    def generate():
        last_data = None
        while True:
            patients = Patient.query.filter(
                Patient.status.in_(["Waiting for Doctor", "In Consultation"])
            ).order_by(Patient.registration_time).all()
            
            patient_list = []
            for patient in patients:
                estimated_wait_time = patient.queue_position * 5
                
                patient_list.append({
                    "id": patient.unique_4digit,
                    "name": patient.name,
                    "assignedDoctor": patient.assigned_doctor.name if patient.assigned_doctor else "Unassigned",
                    "queuePosition": patient.queue_position,
                    "estimatedWaitTime": estimated_wait_time,
                    "status": patient.status
                })
            
            current_data = json.dumps(patient_list)
            if current_data != last_data:
                yield f"data: {current_data}\n\n"
                last_data = current_data
            
            time.sleep(2)
    
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

# Doctor routes
@app.route('/api/doctor/queue')
@login_required
def get_doctor_queue():
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    patients = Patient.query.filter_by(
        assigned_doctor_id=current_user.id,
        status="Waiting for Doctor"
    ).order_by(Patient.queue_position).all()
    
    patient_list = []
    for patient in patients:
        wait_time = (datetime.utcnow() - patient.registration_time).total_seconds() // 60
        
        patient_list.append({
            "id": patient.unique_4digit,
            "name": patient.name,
            "queuePosition": patient.queue_position,
            "waitTime": int(wait_time),
            "contact": patient.contact
        })
    
    return jsonify(patient_list)

@app.route('/api/doctor/queue/events')
@login_required
def doctor_queue_events():
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    def generate():
        last_data = None
        while True:
            patients = Patient.query.filter_by(
                assigned_doctor_id=current_user.id,
                status="Waiting for Doctor"
            ).order_by(Patient.queue_position).all()
            
            patient_list = []
            for patient in patients:
                wait_time = (datetime.utcnow() - patient.registration_time).total_seconds() // 60
                
                patient_list.append({
                    "id": patient.unique_4digit,
                    "name": patient.name,
                    "queuePosition": patient.queue_position,
                    "waitTime": int(wait_time),
                    "contact": patient.contact
                })
            
            current_data = json.dumps(patient_list)
            if current_data != last_data:
                yield f"data: {current_data}\n\n"
                last_data = current_data
            
            time.sleep(2)
    
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route('/api/doctor/start-consultation', methods=['POST'])
@login_required
def start_consultation():
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    patient_id = data.get('patientId')
    
    if not patient_id:
        return jsonify({"error": "Missing patient ID"}), 400
    
    patient = Patient.query.filter_by(unique_4digit=patient_id).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    if patient.assigned_doctor_id != current_user.id:
        return jsonify({"error": "Patient not assigned to you"}), 403
    
    patient.status = "In Consultation"
    db.session.commit()
    
    return jsonify({"success": True})

@app.route('/api/doctor/complete-consultation', methods=['POST'])
@login_required
def complete_consultation():
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    patient_id = data.get('patientId')
    prescription_text = data.get('prescription', '')
    
    if not patient_id:
        return jsonify({"error": "Missing patient ID"}), 400
    
    patient = Patient.query.filter_by(unique_4digit=patient_id).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    if patient.assigned_doctor_id != current_user.id:
        return jsonify({"error": "Patient not assigned to you"}), 403
    
    # Update patient status
    patient.status = "Ready for Pharmacy"
    
    # Add prescription if provided
    if prescription_text:
        # Simple parsing of prescription text
        medicines = [med.strip() for med in prescription_text.split(',')]
        for medicine in medicines:
            if medicine:
                prescription = Prescription(patient_id=patient.id, medicine=medicine)
                db.session.add(prescription)
    
    # Update queue positions for remaining patients
    waiting_patients = Patient.query.filter_by(
        assigned_doctor_id=current_user.id,
        status="Waiting for Doctor"
    ).order_by(Patient.queue_position).all()
    
    for i, p in enumerate(waiting_patients):
        p.queue_position = i + 1
    
    # Set pharmacy queue position
    pharmacy_count = Patient.query.filter_by(status="Ready for Pharmacy").count()
    patient.queue_position = pharmacy_count + 1
    
    db.session.commit()
    
    return jsonify({"success": True})

# Pharmacy routes
@app.route('/api/pharmacy/queue')
@login_required
def get_pharmacy_queue():
    if current_user.role != 'pharmacist':
        return jsonify({"error": "Unauthorized"}), 403
    
    patients = Patient.query.filter_by(status="Ready for Pharmacy").order_by(Patient.queue_position).all()
    
    patient_list = []
    for patient in patients:
        prescriptions = [p.medicine for p in patient.prescriptions]
        prescription_text = ", ".join(prescriptions)
        
        patient_list.append({
            "id": patient.unique_4digit,
            "name": patient.name,
            "queuePosition": patient.queue_position,
            "prescription": prescription_text,
            "contact": patient.contact
        })
    
    return jsonify(patient_list)

@app.route('/api/pharmacy/queue/events')
@login_required
def pharmacy_queue_events():
    if current_user.role != 'pharmacist':
        return jsonify({"error": "Unauthorized"}), 403
    
    def generate():
        last_data = None
        while True:
            patients = Patient.query.filter_by(status="Ready for Pharmacy").order_by(Patient.queue_position).all()
            
            patient_list = []
            for patient in patients:
                prescriptions = [p.medicine for p in patient.prescriptions]
                prescription_text = ", ".join(prescriptions)
                
                patient_list.append({
                    "id": patient.unique_4digit,
                    "name": patient.name,
                    "queuePosition": patient.queue_position,
                    "prescription": prescription_text,
                    "contact": patient.contact
                })
            
            current_data = json.dumps(patient_list)
            if current_data != last_data:
                yield f"data: {current_data}\n\n"
                last_data = current_data
            
            time.sleep(2)
    
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route('/api/pharmacy/complete', methods=['POST'])
@login_required
def complete_pharmacy():
    if current_user.role != 'pharmacist':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    patient_id = data.get('patientId')
    
    if not patient_id:
        return jsonify({"error": "Missing patient ID"}), 400
    
    patient = Patient.query.filter_by(unique_4digit=patient_id).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Update patient status
    patient.status = "Checked Out"
    patient.queue_position = 0
    
    # Update queue positions for remaining pharmacy patients
    pharmacy_patients = Patient.query.filter_by(status="Ready for Pharmacy").order_by(Patient.queue_position).all()
    
    for i, p in enumerate(pharmacy_patients):
        if p.id != patient.id:  # Skip the current patient
            p.queue_position = i + 1
    
    db.session.commit()
    
    return jsonify({"success": True})

# Admin routes
@app.route('/api/admin/staff')
@login_required
def get_staff():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    staff = User.query.all()
    staff_list = []
    
    for user in staff:
        staff_list.append({
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "role": user.role,
            "active": user.active,
            "node_id": user.node_id
        })
    
    return jsonify(staff_list)

@app.route('/api/admin/create-staff', methods=['POST'])
@login_required
def create_staff():
    if current_user.role != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role')
        node_id = data.get('node_id') if role == 'receptionist' else None
        
        if not username or not password or not name or not role:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"success": False, "error": "Username already exists"}), 400
        
        # Create new user
        new_user = User(username=username, name=name, role=role, node_id=node_id)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"Created new staff account: {username} with role {role}")
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating staff: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/system-stats')
@login_required
def get_system_stats():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get total patients today
    today = datetime.utcnow().date()
    total_patients_today = Patient.query.filter(
        db.func.date(Patient.registration_time) == today
    ).count()
    
    # Get active patients
    active_patients = Patient.query.filter(
        Patient.status != "Checked Out"
    ).count()
    
    # Calculate average wait time
    waiting_patients = Patient.query.filter_by(status="Waiting for Doctor").all()
    wait_times = []
    for patient in waiting_patients:
        wait_time = (datetime.utcnow() - patient.registration_time).total_seconds() // 60
        wait_times.append(wait_time)
    
    average_wait_time = int(sum(wait_times) / len(wait_times)) if wait_times else 0
    
    # Queue status
    doctor_queue = Patient.query.filter_by(status="Waiting for Doctor").count()
    pharmacy_queue = Patient.query.filter_by(status="Ready for Pharmacy").count()
    
    doctor_queue_status = "Normal"
    if doctor_queue > 10:
        doctor_queue_status = "Overloaded"
    elif doctor_queue > 5:
        doctor_queue_status = "Busy"
    
    pharmacy_queue_status = "Normal"
    if pharmacy_queue > 10:
        pharmacy_queue_status = "Overloaded"
    elif pharmacy_queue > 5:
        pharmacy_queue_status = "Busy"
    
    return jsonify({
        "totalPatientsToday": total_patients_today,
        "activePatients": active_patients,
        "averageWaitTime": average_wait_time,
        "systemStatus": "Operational",
        "queues": [
            {
                "name": "Doctor Queue",
                "patientsWaiting": doctor_queue,
                "averageWaitTime": average_wait_time,
                "status": doctor_queue_status
            },
            {
                "name": "Pharmacy Queue",
                "patientsWaiting": pharmacy_queue,
                "averageWaitTime": 10,  # Placeholder
                "status": pharmacy_queue_status
            }
        ]
    })

@app.route('/api/admin/system-stats/events')
@login_required
def system_stats_events():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    def generate():
        try:
            while True:
                try:
                    # Get total patients today
                    today = datetime.utcnow().date()
                    total_patients_today = Patient.query.filter(
                        db.func.date(Patient.registration_time) == today
                    ).count()
                    
                    # Get active patients
                    active_patients = Patient.query.filter(
                        Patient.status != "Checked Out"
                    ).count()
                    
                    # Calculate average wait time
                    waiting_patients = Patient.query.filter_by(status="Waiting for Doctor").all()
                    wait_times = []
                    for patient in waiting_patients:
                        wait_time = (datetime.utcnow() - patient.registration_time).total_seconds() // 60
                        wait_times.append(wait_time)
                    
                    average_wait_time = int(sum(wait_times) / len(wait_times)) if wait_times else 0
                    
                    # Queue status
                    doctor_queue = Patient.query.filter_by(status="Waiting for Doctor").count()
                    pharmacy_queue = Patient.query.filter_by(status="Ready for Pharmacy").count()
                    
                    doctor_queue_status = "Normal"
                    if doctor_queue > 10:
                        doctor_queue_status = "Overloaded"
                    elif doctor_queue > 5:
                        doctor_queue_status = "Busy"
                    
                    pharmacy_queue_status = "Normal"
                    if pharmacy_queue > 10:
                        pharmacy_queue_status = "Overloaded"
                    elif pharmacy_queue > 5:
                        pharmacy_queue_status = "Busy"
                    
                    data = {
                        "totalPatientsToday": total_patients_today,
                        "activePatients": active_patients,
                        "averageWaitTime": average_wait_time,
                        "systemStatus": "Operational",
                        "queues": [
                            {
                                "name": "Doctor Queue",
                                "patientsWaiting": doctor_queue,
                                "averageWaitTime": average_wait_time,
                                "status": doctor_queue_status
                            },
                            {
                                "name": "Pharmacy Queue",
                                "patientsWaiting": pharmacy_queue,
                                "averageWaitTime": 10,  # Placeholder
                                "status": pharmacy_queue_status
                            }
                        ]
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                    time.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    logger.error(f"Error in system stats SSE: {str(e)}")
                    yield f"data: {json.dumps({'error': 'Failed to fetch system stats'})}\n\n"
                    break
        except GeneratorExit:
            logger.info("Client disconnected from system stats SSE")
        except Exception as e:
            logger.error(f"Fatal error in system stats SSE: {str(e)}")
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/admin/mutex-logs')
@login_required
def get_mutex_logs():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        logs = MutexLog.query.order_by(MutexLog.created_at.desc()).limit(100).all()
        formatted_logs = [{
            'id': log.id,
            'node_id': log.node_id,
            'event': log.event,
            'timestamp': log.timestamp,
            'target_node': log.target_node,
            'created_at': log.created_at.strftime("%H:%M:%S")  # Format as HH:MM:SS
        } for log in logs]
        return jsonify(formatted_logs)
    except Exception as e:
        logger.error(f"Error fetching mutex logs: {str(e)}")
        return jsonify({'error': 'Failed to fetch mutex logs'}), 500

@app.route('/api/admin/mutex-logs/events')
@login_required
def mutex_logs_events():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    def generate():
        last_id = 0
        try:
            while True:
                try:
                    # Get new logs since last check
                    new_logs = MutexLog.query.filter(MutexLog.id > last_id)\
                        .order_by(MutexLog.created_at.desc())\
                        .limit(10).all()
                    
                    if new_logs:
                        # Update last_id to the most recent log
                        last_id = new_logs[0].id
                        
                        # Format and yield new logs
                        for log in reversed(new_logs):  # Send oldest first
                            log_data = {
                                'id': log.id,
                                'node_id': log.node_id,
                                'event': log.event,
                                'timestamp': log.timestamp,
                                'target_node': log.target_node,
                                'created_at': log.created_at.strftime("%H:%M:%S")
                            }
                            yield f"data: {json.dumps(log_data)}\n\n"
                    
                    time.sleep(1)  # Check every second
                except Exception as e:
                    logger.error(f"Error in mutex logs SSE: {str(e)}")
                    yield f"data: {json.dumps({'error': 'Failed to fetch mutex logs'})}\n\n"
                    break
        except GeneratorExit:
            logger.info("Client disconnected from mutex logs SSE")
        except Exception as e:
            logger.error(f"Fatal error in mutex logs SSE: {str(e)}")
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/receptionist/register-check', methods=['POST'])
def register_patient_check():
    """A diagnostic route to check patient registration issues"""
    # Check if user is authenticated
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return jsonify({
            "success": False, 
            "error": "Not authenticated",
            "auth_status": "Not logged in"
        }), 401
        
    # Check user role
    if current_user.role != 'receptionist':
        return jsonify({
            "success": False, 
            "error": "Wrong role",
            "auth_status": f"Logged in as {current_user.role}, need receptionist role"
        }), 403
    
    # Get request data
    data = request.get_json()
    
    return jsonify({
        "success": True,
        "message": "Authentication check passed",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        },
        "request_data": data
    })

@app.route('/api/admin/staff/<int:staff_id>', methods=['PUT'])
@login_required
def update_staff(staff_id):
    if current_user.role != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        staff = User.query.get(staff_id)
        if not staff:
            return jsonify({"success": False, "error": "Staff not found"}), 404
        
        data = request.get_json()
        
        # Update basic info
        staff.name = data.get('name', staff.name)
        staff.username = data.get('username', staff.username)
        staff.role = data.get('role', staff.role)
        
        # Update node_id if role is receptionist
        if staff.role == 'receptionist':
            staff.node_id = data.get('node_id')
        else:
            staff.node_id = None
        
        # Update password if provided
        if 'password' in data and data['password']:
            staff.set_password(data['password'])
        
        db.session.commit()
        logger.info(f"Updated staff account: {staff.username}")
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating staff: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/staff/<int:staff_id>/toggle', methods=['POST'])
@login_required
def toggle_staff_status(staff_id):
    if current_user.role != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        staff = User.query.get(staff_id)
        if not staff:
            return jsonify({"success": False, "error": "Staff not found"}), 404
        
        # Don't allow deactivating the last active admin
        if staff.role == 'admin' and staff.active:
            active_admins = User.query.filter_by(role='admin', active=True).count()
            if active_admins <= 1:
                return jsonify({
                    "success": False, 
                    "error": "Cannot deactivate the last active admin account"
                }), 400
        
        staff.active = not staff.active
        db.session.commit()
        logger.info(f"Toggled staff status for {staff.username} to {staff.active}")
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling staff status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Initialize database
@app.before_first_request
def initialize_database():
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create default admin user
        admin = User(username='admin', name='Administrator', role='admin')
        admin.set_password('admin123')
        
        # Create default receptionist
        receptionist = User(username='reception', name='Receptionist', role='receptionist', node_id='node_1')
        receptionist.set_password('reception123')
        
        # Create default doctor
        doctor = User(username='doctor', name='Dr. Smith', role='doctor')
        doctor.set_password('doctor123')
        
        # Create default pharmacist
        pharmacist = User(username='pharmacy', name='Pharmacist', role='pharmacist')
        pharmacist.set_password('pharmacy123')
        
        db.session.add(admin)
        db.session.add(receptionist)
        db.session.add(doctor)
        db.session.add(pharmacist)
        db.session.commit()
        
        logger.info("Created default users")

@app.route('/debug-info')
def debug_info():
    template_folder = app.template_folder
    static_folder = app.static_folder
    
    template_files = []
    if os.path.exists(template_folder):
        template_files = os.listdir(template_folder)
    
    static_files = []
    if os.path.exists(static_folder):
        static_files = os.listdir(static_folder)
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint}: {rule}")
    
    config_items = {k: str(v) for k, v in app.config.items() if k not in ['SECRET_KEY']}
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Debug Info</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1, h2 {{ color: #2c3e50; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .section {{ background-color: #f9f9f9; padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
            code {{ background: #eee; padding: 2px 5px; border-radius: 3px; }}
            ul {{ padding-left: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Flask Application Debug Information</h1>
            
            <div class="section">
                <h2>Application Configuration</h2>
                <ul>
                    <li>Debug Mode: <code>{app.debug}</code></li>
                    <li>Template Folder: <code>{template_folder}</code></li>
                    <li>Static Folder: <code>{static_folder}</code></li>
                    <li>Node ID: <code>{node_id}</code></li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Templates ({len(template_files)} files)</h2>
                <ul>
                    {''.join(f'<li>{file}</li>' for file in template_files)}
                </ul>
            </div>
            
            <div class="section">
                <h2>Static Files ({len(static_files)} files)</h2>
                <ul>
                    {''.join(f'<li>{file}</li>' for file in static_files)}
                </ul>
            </div>
            
            <div class="section">
                <h2>Available Routes ({len(routes)})</h2>
                <ul>
                    {''.join(f'<li><code>{route}</code></li>' for route in routes)}
                </ul>
            </div>
            
            <div class="section">
                <h2>App Configuration</h2>
                <ul>
                    {''.join(f'<li><strong>{k}</strong>: <code>{v}</code></li>' for k, v in config_items.items())}
                </ul>
            </div>
            
            <div class="section">
                <h2>Useful Links</h2>
                <ul>
                    <li><a href="/direct">Direct HTML Page</a></li>
                    <li><a href="/test">Test Page</a></li>
                    <li><a href="/">Home Page</a></li>
                    <li><a href="/login">Login Page</a></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/pharmacy-test')
def pharmacy_test():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pharmacy Test Page</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #2c3e50; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .login-link { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }
            .debug { background-color: #f9f9f9; padding: 15px; border-left: 4px solid #3498db; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Pharmacy Test Page</h1>
            <p>This is a test page for the pharmacy portal without authentication requirements.</p>
            
            <div class="debug">
                <h3>Login Status:</h3>
                <p>Is user authenticated: <strong>''' + str(hasattr(current_user, 'is_authenticated') and current_user.is_authenticated) + '''</strong></p>
                ''' + (f'<p>Username: <strong>{current_user.username}</strong></p>' if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else '') + '''
                ''' + (f'<p>Role: <strong>{current_user.role}</strong></p>' if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else '') + '''
            </div>
            
            <p>To access the actual pharmacy portal, you need to be logged in as a pharmacist.</p>
            <a href="/login" class="login-link">Go to Login</a>
        </div>
    </body>
    </html>
    '''

@app.route('/pharmacist')
def pharmacist_redirect():
    """Redirect from /pharmacist to /pharmacy page"""
    return redirect(url_for('pharmacy_portal'))

@app.route('/staff')
def staff_login():
    """Separate route for staff login"""
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)

# Custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page Not Found</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #e74c3c;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 20px;
            }
            .debug-info {
                background-color: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #e74c3c;
                margin-top: 20px;
            }
            .links {
                margin-top: 30px;
            }
            .links a {
                display: block;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist or has been moved.</p>
            
            <div class="debug-info">
                <h3>Debug Information:</h3>
                <p>Requested URL: <strong>''' + request.url + '''</strong></p>
                <p>Method: <strong>''' + request.method + '''</strong></p>
            </div>
            
            <div class="links">
                <h2>Try these pages instead:</h2>
                <a href="/direct">Direct HTML Page</a>
                <a href="/login">Login Page</a>
                <a href="/test">Test Page</a>
                <a href="/">Home Page</a>
            </div>
            
            <a href="/" class="btn">Go to Home</a>
        </div>
    </body>
    </html>
    ''', 404

