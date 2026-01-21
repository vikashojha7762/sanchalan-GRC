# Backend Server Startup Guide

## ✅ Backend Server Started

The backend server has been started and is running on **http://localhost:8000**

## Quick Start Methods

### Method 1: Using Batch File (Windows)
```bash
cd backend
start_server.bat
```

### Method 2: Using PowerShell Script
```bash
cd backend
.\start_server.ps1
```

### Method 3: Manual Start
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify Server is Running

### Option 1: Browser
Open in your browser:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

### Option 2: PowerShell
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

### Option 3: Command Line
```bash
curl http://localhost:8000/health
```

## Expected Response

When the server is running, you should see:
```json
{
  "status": "healthy",
  "message": "SANCHALAN AI GRC Platform is running"
}
```

## Troubleshooting

### Issue: Port 8000 Already in Use

**Solution 1: Find and Kill Process**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Solution 2: Use Different Port**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
Then update `frontend/.env`:
```
VITE_API_BASE_URL=http://localhost:8001
```

### Issue: Database Connection Error

**Check:**
1. PostgreSQL is running
2. `DATABASE_URL` in `backend/.env` is correct
3. Database exists: `GRC_Database`

**Test Connection:**
```bash
cd backend
python -c "from app.db import engine; print('Database connected')"
```

### Issue: Module Not Found

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: .env File Not Found

**Solution:**
1. Create `backend/.env` file
2. Copy content from `backend/CREATE_ENV_FILE.txt`
3. Save the file

## Server Status Indicators

### ✅ Server Running Successfully
- Health endpoint returns 200 OK
- API docs accessible at `/docs`
- No error messages in terminal

### ❌ Server Not Running
- Connection refused errors
- Port not accessible
- Check terminal for error messages

## Auto-Start on System Boot (Optional)

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "When computer starts"
4. Action: Start program
5. Program: `C:\path\to\python.exe`
6. Arguments: `-m uvicorn app.main:app --host 0.0.0.0 --port 8000`
7. Start in: `C:\path\to\backend`

## Development Tips

1. **Keep Server Running**: Don't close the terminal while developing
2. **Auto-Reload**: Server auto-reloads on code changes (--reload flag)
3. **Check Logs**: Watch terminal for error messages
4. **API Testing**: Use Swagger UI at `/docs` for testing endpoints

## Next Steps

1. ✅ Backend server is running
2. ✅ Start frontend: `cd frontend && npm run dev`
3. ✅ Test signup/login functionality
4. ✅ Verify API endpoints work
