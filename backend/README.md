# Backend - SANCHALAN AI GRC Platform

FastAPI backend for the SANCHALAN AI GRC platform.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
Create a `.env` file in the `backend` directory with the following content:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5433/GRC_Database
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=sanchalan-index
JWT_SECRET=change_this_to_a_secure_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=http://localhost:5173
```

**Note:** The `.env` file is hidden (starts with a dot). To create it:
- In VS Code/Cursor: Right-click → New File → Name it `.env`
- Or use the `CREATE_ENV_FILE.txt` in this directory for instructions

3. Verify .env connection:
```bash
python test_env_connection.py
```

4. Run database migrations:
```bash
python -m alembic upgrade head
```

## Running the Server

To run the backend server:

```bash
cd backend
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

API documentation available at `http://localhost:8000/docs`

## Connection Flow

```
.env file (backend/.env)
    ↓
app/db.py → Loads DATABASE_URL → Creates SQLAlchemy engine
app/core/config.py → Loads all env vars → Creates Settings object
    ↓
app/services/ai_service.py → Uses settings.OPENAI_API_KEY
app/services/pinecone_service.py → Uses settings.PINECONE_API_KEY
app/main.py → Uses settings for CORS and all configurations
```

## Troubleshooting

If you see "DATABASE_URL is missing" error:
1. Verify `.env` file exists in `backend/` folder
2. Check file name is exactly `.env` (with the dot)
3. Run `python test_env_connection.py` to diagnose issues
