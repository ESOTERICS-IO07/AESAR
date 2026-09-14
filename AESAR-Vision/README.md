# AESAR-Vision

Standalone Phase 1 Vision Intelligence Lab: camera selection and low-latency live preview only.

## Run the backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and select a local webcam or IP camera URL. The browser receives only an MJPEG stream from FastAPI; it never accesses a hardware camera directly.
