# Hospital Queue Management System

A distributed hospital queue management system with mutex analysis capabilities.

## Overview

This project implements a distributed hospital queue management system with the following features:

- Patient registration and queue management
- Role-based access control (Admin, Receptionist, Doctor, Pharmacist)
- Distributed mutual exclusion algorithm for critical section access
- Real-time mutex event logging and visualization
- Multi-node architecture with node synchronization

## Components

### Backend (Flask)

- Flask-based REST API
- SQLite database for data persistence
- Ricart-Agrawala algorithm for distributed mutual exclusion
- Real-time event streaming using Server-Sent Events (SSE)

### Frontend (Next.js)

- Modern UI for patient portal and staff interfaces
- Real-time updates using SSE
- Role-specific dashboards

### Mutex Analysis Tool

- Visualization of mutex events and node interactions
- Timeline analysis of critical section access
- Logical clock progression tracking
- Node interaction heatmaps

## Getting Started

### Prerequisites

- Python 3.6+
- Node.js 14+
- npm or yarn

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hospital-queue-system.git
   cd hospital-queue-system
   ```

2. Install backend dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

### Running the Application

1. Start the backend server:
   ```
   python run_node1_debug.py
   ```

2. Start the frontend development server:
   ```
   cd frontend
   npm run dev
   ```

3. Access the application at http://localhost:3000

## Mutex Analysis

To analyze mutex events, use the mutex analysis tool:

```
python mutex_analysis.py [options]
```

See [mutex_analysis_README.md](mutex_analysis_README.md) for detailed instructions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Ricart-Agrawala algorithm for distributed mutual exclusion
- Flask and Next.js communities for excellent documentation 