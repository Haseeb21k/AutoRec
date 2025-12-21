# AutoRec: AI-Powered Financial Reconciliation System

**AutoRec** is a modern, full-stack application designed to automate the painful process of reconciling bank statements against internal ledgers. It leverages **Generative AI (Google Gemini)** to parse unstructured documents and uses a multi-stage matching engine to identify discrepancies in real-time.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![React](https://img.shields.io/badge/react-18-cyan.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)

## 🚀 Key Features

*   **Universal File Import**: Support for **CSV**, **Excel**, **MT940**, and **PDF** files.
*   **AI-Driven Parsing**: Uses **Google Gemini 1.5 Flash** to intelligently extract transaction data from complex PDF bank statements.
*   **Smart Matching Engine**:
    *   **Pass 1**: Exact Match (Amount + Date + Description).
    *   **Pass 2**: Fuzzy Match (Amount + Date + Partial Description).
    *   **Pass 3**: AI-Suggested Matches (Coming Soon).
*   **Real-Time Dashboard**: Live reconciliation feed via **WebSockets**, showing matches as they happen.
*   **Role-Based Access Control (RBAC)**:
    *   **Superusers**: Full access (Uploads, Reconciliation Run, User Management).
    *   **Standard Users**: Read-only access to dashboard and reports.
*   **Secure**: JWT Authentication and environment-secured credentials.

## 🛠️ Tech Stack

### Backend
*   **Framework**: FastAPI (Python)
*   **Database**: PostgreSQL (Production) / SQLite (Dev)
*   **ORM**: SQLAlchemy
*   **AI Integration**: Google Generative AI (Gemini)
*   **Testing**: Pytest

### Frontend
*   **Library**: React (Vite)
*   **Styling**: Tailwind CSS
*   **Icons**: Lucide React
*   **State**: React Hooks & Context API

### DevOps
*   **Containerization**: Docker & Docker Compose
*   **Server**: Nginx (Reverse Proxy)

## 📦 Installation & Setup

### Prerequisites
*   Docker Desktop installed
*   Git installed
*   A Google Gemini API Key

### Option 1: Docker (Recommended)

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Haseeb21k/AutoRec.git
    cd AutoRec
    ```

2.  **Configure Environment**
    Create a `.env` file in the `backend/` directory:
    ```env
    API_KEY=your_gemini_api_key_here
    SECRET_KEY=your_secure_random_string
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    # Docker automatically injects DATABASE_URL for Postgres
    ```

3.  **Run with Docker Compose**
    ```bash
    docker-compose up --build
    ```

4.  **Access the Application**
    *   **Frontend**: http://localhost
    *   **Backend API Docs**: http://localhost:8000/docs

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🔒 Security

*   **Authentication**: OAuth2 with Password Flow (JWT).
*   **Session Management**: 8-hour default session, extendable to 30 days with "Remember Me".
*   **Sensitive Data**: All credentials loaded via environment variables; `.env` is git-ignored.

## 📄 License

This project is licensed under the MIT License.
