# SANCHALAN AI GRC Platform

<div align="center">

**AI-powered Governance, Risk, and Compliance platform for modern enterprises**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Pinecone](https://img.shields.io/badge/Pinecone-430098?style=for-the-badge&logo=pinecone&logoColor=white)](https://www.pinecone.io/)

</div>

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

SANCHALAN is an intelligent Governance, Risk, and Compliance (GRC) platform that leverages AI to help organizations manage their compliance frameworks, policies, gaps, and remediation efforts. The platform provides automated gap analysis, policy management, knowledge base integration, and AI-powered chat assistance.

### Key Capabilities

- **Framework Management**: Support for multiple compliance frameworks (ISO 27001, SOC 2, COBIT, etc.)
- **Policy Management**: Upload, review, and manage organizational policies with AI-powered indexing
- **Gap Analysis**: Automated identification and tracking of compliance gaps
- **Knowledge Base**: Centralized repository for compliance documents and artifacts
- **AI Chat Assistant**: Intelligent assistant for compliance queries
- **Dashboard & Reporting**: Comprehensive dashboards and risk gap reports

## ✨ Features

### Core Features

- 🔐 **User Authentication & Authorization**: Secure JWT-based authentication with role-based access control
- 📊 **Compliance Frameworks**: Manage multiple compliance frameworks and their controls
- 📄 **Policy Management**: 
  - Upload and manage policies with version control
  - Policy approval workflow
  - AI-powered policy indexing and search
- 🔍 **Gap Analysis**:
  - Automated gap identification
  - Gap severity classification
  - Remediation tracking
- 📚 **Knowledge Base**:
  - Document upload and management
  - Vector-based semantic search
  - Multiple document format support (PDF, DOCX)
- 💬 **AI Chat Assistant**: 
  - Natural language queries
  - Context-aware responses
  - Integration with knowledge base
- 📈 **Dashboard**: 
  - Real-time compliance metrics
  - Framework coverage statistics
  - Gap and policy status overview
- 📋 **Reports**: Comprehensive risk gap reports and compliance summaries
- 📎 **Artifact Management**: Upload and manage compliance artifacts

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **AI/ML**:
  - OpenAI API (for embeddings and GPT)
  - Pinecone (vector database for semantic search)
- **File Processing**: PyPDF2, pdfplumber, python-docx

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios

### Infrastructure
- **Database**: PostgreSQL
- **Vector Database**: Pinecone
- **API**: RESTful API with FastAPI

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.8+ ([Download](https://www.python.org/downloads/))
- **Node.js** 16+ and npm ([Download](https://nodejs.org/))
- **PostgreSQL** 12+ ([Download](https://www.postgresql.org/download/))
- **Git** ([Download](https://git-scm.com/downloads))

### Required Accounts

- **OpenAI API Key** ([Get API Key](https://platform.openai.com/api-keys))
- **Pinecone Account** ([Sign Up](https://www.pinecone.io/))

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Sanchalan.git
cd Sanchalan
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb GRC_Database

# Or using psql:
psql -U postgres
CREATE DATABASE "GRC_Database";
\q
```

## ⚙️ Configuration

### Backend Configuration

1. **Create `.env` file** in the `backend` directory:

```bash
cd backend
cp .env.example .env
```

2. **Edit `backend/.env`** with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/GRC_Database

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=sanchalan-index

# JWT Configuration
JWT_SECRET=change_this_to_a_secure_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS Configuration
BACKEND_CORS_ORIGINS=http://localhost:5173
```

**Note**: 
- Replace `YOUR_PASSWORD` with your PostgreSQL password
- URL-encode special characters in password (e.g., `@` becomes `%40`)
- Generate a strong random string for `JWT_SECRET` in production

### Frontend Configuration

1. **Create `.env` file** in the `frontend` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Database Migrations

```bash
cd backend
python -m alembic upgrade head
```

## 🏃 Running the Application

### Start Backend Server

**Option 1: Using Batch Script (Windows)**
```bash
cd backend
start_server.bat
```

**Option 2: Using PowerShell Script**
```bash
cd backend
.\start_server.ps1
```

**Option 3: Manual Start**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: **http://localhost:8000**

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at: **http://localhost:5173**

### Verify Installation

1. **Backend Health Check**: 
   - Open: http://localhost:8000/health
   - Should return: `{"status":"healthy","message":"SANCHALAN AI GRC Platform is running"}`

2. **API Documentation**: 
   - Open: http://localhost:8000/docs
   - Interactive Swagger UI for API testing

3. **Frontend**: 
   - Open: http://localhost:5173
   - Sign up or sign in to access the platform

## 📁 Project Structure

```
Sanchalan/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   │   └── v1/        # API version 1
│   │   ├── core/          # Core configuration
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic services
│   │   ├── utils/         # Utility functions
│   │   └── main.py        # FastAPI application
│   ├── alembic/           # Database migrations
│   ├── uploads/           # Uploaded files
│   ├── storage/           # Storage directory
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment variables template
│
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── lib/           # Utility libraries
│   │   └── main.jsx       # Entry point
│   ├── package.json       # Node dependencies
│   └── .env.example       # Environment variables template
│
└── README.md              # This file
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Main Endpoints

- **Authentication**: `/api/v1/auth/*`
  - POST `/register` - User registration
  - POST `/login` - User login
  - GET `/me` - Get current user

- **Frameworks**: `/api/v1/frameworks/*`
  - GET `/` - List all frameworks
  - GET `/{framework_id}/control-groups` - Get control groups
  - GET `/{framework_id}/controls` - Get controls

- **Policies**: `/api/v1/policies/*`
  - POST `/upload` - Upload policy
  - GET `/` - List policies
  - GET `/{policy_id}` - Get policy details
  - PUT `/{policy_id}` - Update policy
  - DELETE `/{policy_id}` - Delete policy

- **Gaps**: `/api/v1/gaps/*`
  - GET `/` - List gaps
  - POST `/` - Create gap
  - PUT `/{gap_id}` - Update gap

- **Knowledge Base**: `/api/v1/knowledge-base/*`
  - POST `/upload` - Upload document
  - GET `/` - List documents
  - GET `/{doc_id}` - Get document

- **Chat**: `/api/v1/chat/*`
  - POST `/query` - Send chat query

- **Dashboard**: `/api/v1/dashboard/*`
  - GET `/summary` - Get dashboard summary

### Interactive API Docs

Visit **http://localhost:8000/docs** for interactive Swagger UI documentation.

## 💡 Usage

### Getting Started

1. **Sign Up**: Create a new account at http://localhost:5173/signup
2. **Onboarding**: Complete the onboarding process to set up your company
3. **Select Frameworks**: Choose compliance frameworks relevant to your organization
4. **Upload Policies**: Start uploading your organizational policies
5. **Gap Analysis**: Run gap analysis to identify compliance gaps
6. **Knowledge Base**: Upload compliance documents to the knowledge base
7. **Chat Assistant**: Use the AI chat assistant for compliance queries

### Key Workflows

#### Policy Management
1. Navigate to **Policies** page
2. Click **Upload Policy**
3. Fill in policy details and upload document
4. Policy is automatically indexed for search
5. Policy goes through approval workflow

#### Gap Analysis
1. Navigate to **Gap Analysis** page
2. Select framework and controls
3. System identifies gaps automatically
4. Review and assign remediation tasks
5. Track remediation progress

#### Knowledge Base
1. Navigate to **Knowledge Base** page
2. Upload compliance documents (PDF, DOCX)
3. Documents are processed and indexed
4. Use semantic search to find relevant information

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Follow ESLint rules for JavaScript/React code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

## 🔒 Security

- **Never commit `.env` files** - They contain sensitive credentials
- Use strong, unique passwords
- Rotate API keys regularly
- Keep dependencies updated
- Use HTTPS in production
- Implement proper access controls

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For issues, questions, or contributions:

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/Sanchalan/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/Sanchalan/discussions)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React team for the powerful UI library
- OpenAI for AI capabilities
- Pinecone for vector database services
- All open-source contributors

---

<div align="center">

**Built with ❤️ for better Governance, Risk, and Compliance management**

[⬆ Back to Top](#sanchalan-ai-grc-platform)

</div>
