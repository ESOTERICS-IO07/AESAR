@echo off
echo Starting ARACHNID Backend Service...
cd ..
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
