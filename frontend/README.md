# SANCHALAN Frontend

React (Vite) frontend for the SANCHALAN AI GRC Platform.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
Create a `.env` file in the frontend directory:
```
VITE_API_BASE_URL=http://localhost:8000
```

3. Run development server:
```bash
npm run dev
```

## Features

- **Authentication**: Sign in and Sign up pages
- **Onboarding Wizard**: 8-step onboarding process
- **Dashboard**: Compliance monitoring with charts and statistics
- **Gap Management**: View, update, and create remediations for gaps
- **Artifact Upload**: Upload documents and evidence
- **Approvals Workflow**: Review and approve pending policies
- **AI Chat Assistant**: RAG-powered chat for GRC questions

## Tech Stack

- React 18
- Vite
- React Router
- Axios
- Tailwind CSS
- Recharts
- Lucide React Icons
