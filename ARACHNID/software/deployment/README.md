# ARACHNID Rover Deployment Guide

## Quick Start Sequence

### 1. Install Backend Dependencies
```bash
cd software
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies
```bash
cd software/frontend
npm install
```

### 3. Choose ROS2 Provider Mode
In `software/.env` (or environment variables):
- `ARACHNID_ROS2_PROVIDER=simulated` (For software testing with full kinematics simulator)
- `ARACHNID_ROS2_PROVIDER=real` (For physical rover integration via ROS2 bridge)
- `ARACHNID_ROS2_PROVIDER=mock` (For local lightweight testing)

### 4. Start the Backend
```bash
cd software
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8100 --reload
```
Swagger UI will be available at: [http://127.0.0.1:8100/docs](http://127.0.0.1:8100/docs)

### 5. Start the Frontend Command Center
```bash
cd software/frontend
npm run dev
```
Web application will be accessible at: [http://127.0.0.1:5173](http://127.0.0.1:5173)

### 6. Verify System Health
Open: `GET http://127.0.0.1:8100/api/health`
Expected: `{"status": "ok", "backend": true, "ros2_connected": true}`
