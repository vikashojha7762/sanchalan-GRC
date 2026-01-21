# Environment Variables Setup Guide

This project requires environment variables to be set in two locations:

## Backend Environment Variables

Create `backend/.env` with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5433/GRC_Database

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=sanchalan-index

# JWT Configuration
JWT_SECRET=change_this_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS Configuration
BACKEND_CORS_ORIGINS=http://localhost:5173
```

## Frontend Environment Variables

Create `frontend/.env` with the following variables:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Variable Descriptions

### Backend Variables

- **DATABASE_URL**: PostgreSQL connection string
  - Format: `postgresql+psycopg2://username:password@host:port/database`
  - URL-encode special characters in password (e.g., `@` becomes `%40`)

- **OPENAI_API_KEY**: Your OpenAI API key for embeddings and GPT

- **PINECONE_API_KEY**: Your Pinecone API key for vector database

- **PINECONE_ENVIRONMENT**: Pinecone environment/region (e.g., `us-east-1`)

- **PINECONE_INDEX_NAME**: Name of your Pinecone index

- **JWT_SECRET**: Secret key for JWT token signing (use a strong random string in production)

- **JWT_ALGORITHM**: Algorithm for JWT (default: HS256)

- **ACCESS_TOKEN_EXPIRE_MINUTES**: Token expiration time in minutes

- **BACKEND_CORS_ORIGINS**: Comma-separated list of allowed CORS origins

### Frontend Variables

- **VITE_API_BASE_URL**: Base URL of the FastAPI backend

## Security Notes

⚠️ **Important**: 
- Never commit `.env` files to version control
- `.env` files are already in `.gitignore`
- Change `JWT_SECRET` to a secure random string in production
- Keep your API keys secure and never share them publicly
