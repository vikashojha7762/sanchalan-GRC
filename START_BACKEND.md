# How to Start the Backend Server

## ⚠️ IMPORTANT: Backend Must Be Running

The frontend **requires** the backend server to be running on `http://localhost:8000` before you can use the signup/login features.

## Quick Start (Choose One Method)

### Method 1: Using Batch File (Easiest)
1. Navigate to the `backend` folder
2. Double-click `start_server.bat`
3. Keep the terminal window open (don't close it)

### Method 2: Using PowerShell
1. Open PowerShell
2. Navigate to backend folder:
   ```powershell
   cd "C:\Users\vikas\OneDrive\Desktop\Sanchalan\backend"
   ```
3. Run:
   ```powershell
   .\start_server.ps1
   ```
4. Keep the terminal window open

### Method 3: Manual Command
1. Open Command Prompt or PowerShell
2. Navigate to backend folder:
   ```bash
   cd backend
   ```
3. Run:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Keep the terminal window open

## Verify Server is Running

### Option 1: Browser Test
Open in your browser:
- **http://localhost:8000/health**
- Should show: `{"status":"healthy","message":"SANCHALAN AI GRC Platform is running"}`

### Option 2: PowerShell Test
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

### Option 3: Python Script
```bash
cd backend
python check_server.py
```

## What You Should See

When the server starts successfully, you'll see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
🔍 Loading .env from: C:\Users\vikas\OneDrive\Desktop\Sanchalan\backend\.env
🔍 DATABASE_URL Loaded: postgresql+psycopg2://...
INFO:     Application startup complete.
```

## Common Issues

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Issue: "ModuleNotFoundError: No module named 'uvicorn'"
**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "DATABASE_URL is missing"
**Solution:**
1. Create `backend/.env` file
2. Copy content from `backend/CREATE_ENV_FILE.txt`
3. Save the file
4. Restart the server

### Issue: Database Connection Error
**Solution:**
1. Ensure PostgreSQL is running
2. Verify `DATABASE_URL` in `backend/.env` is correct
3. Check database exists: `GRC_Database`

## Keep Server Running

⚠️ **IMPORTANT**: Keep the terminal/command window open while developing. Closing it will stop the server.

- The server runs in the **foreground** (you'll see logs)
- Press `CTRL+C` to stop the server
- Use `--reload` flag for auto-reload on code changes

## Development Workflow

1. ✅ Start backend server (keep terminal open)
2. ✅ Start frontend: `cd frontend && npm run dev`
3. ✅ Open browser: http://localhost:5173
4. ✅ Test signup/login functionality

## Troubleshooting

If you still see "Unable to connect to server":

1. **Check server is running:**
   ```bash
   netstat -ano | findstr :8000
   ```
   Should show port 8000 is LISTENING

2. **Check server logs:**
   Look at the terminal where you started the server for error messages

3. **Test health endpoint:**
   Open: http://localhost:8000/health in browser

4. **Check firewall:**
   Ensure Windows Firewall isn't blocking port 8000

5. **Restart server:**
   Stop (CTRL+C) and start again

## Quick Reference

| Action | Command |
|--------|---------|
| Start server | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Check if running | `netstat -ano \| findstr :8000` |
| Test health | Open http://localhost:8000/health |
| Stop server | Press `CTRL+C` in terminal |
