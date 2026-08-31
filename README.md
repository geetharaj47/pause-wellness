# MindTrace 

> **Personalized AI for Longitudinal Mental Wellness Monitoring and Self-Reflection**

MindTrace is a research-oriented, privacy-preserving wellness application. Unlike generic therapeutic chatbots, MindTrace uses NLP text analysis to learn an individual's unique historical baseline over time, alerting them to meaningful wellness deviations relative only to their own history. 

This project serves as a final-year B.Tech Computer Science project and is structured to support a rigorous research paper comparing generic vs. personalized longitudinal modeling.

---

## 🚀 Key Features

*   **Daily Check-in & Logs:** Extremely low-friction check-ins logging mood rating, sleep quality, and active life factors (work pressure, health, social life, relationships).
*   **Privacy-First Journaling:** Free-form journal editor that scrubs PII (names, emails, phones) locally before performing text sentiment/emotion extraction.
*   **Longitudinal Pattern Analysis:** Side-by-side execution of **Model A (Generic static thresholds)** and **Model B (Personalized dynamic Z-scores and CUSUM)** to analyze performance improvements.
*   **Mathematical Explainability:** Explanations are derived directly from statistical deviation scores (e.g., standard deviation shifts in fatigue or workload mention rates), ensuring grounded transparency.
*   **Controlled Coping Support:** A curated resource library featuring breathing pacing widgets, thought-reframing helpers, and immediate emergency contact gateways.
*   **Anonymized Researcher Dashboard:** Built-in dashboard exposing overall cohort statistics (F1, Precision, Expected Calibration Error, lead latency) while completely hiding raw journals.

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── auth.py          # Session auth controllers, passlib hashing, JWT
│   │   ├── config.py        # Environment variables loader
│   │   ├── database.py      # SQLModel engine adapter (SQLite / PostgreSQL)
│   │   ├── main.py          # FastAPI application entrypoint
│   │   └── models.py        # Schema definitions
│   ├── Dockerfile
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/           # Pages (Dashboard, Journal, History, Trends, Support)
│   │   ├── App.jsx          # Router & layout controller
│   │   ├── index.css        # Tailwind style loader
│   │   └── main.jsx         # React mounting script
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
├── tests/
│   └── test_backend.py      # Pytest validation scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🛠️ Prerequisites

*   **Python:** 3.12.x or higher
*   **Node.js:** v20.x or higher (npm included)
*   **Git**

---

## 💻 Local Setup & Development

### 1. Backend Server Setup
From the repository root directory, create a virtual environment and run the backend:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run server (automatically initializes SQLite database 'mindtrace.db')
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger documentation will be available locally at: [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Frontend React Setup
Open a new terminal window at the repository root and start Vite:

```bash
# Navigate to frontend directory
cd frontend

# Install package dependencies
npm install

# Start local server
npm run dev
```
The React frontend will load at: [http://localhost:3000](http://localhost:3000).

---

## 🐳 Dockerized Execution

If you have Docker and Docker Compose installed and running, you can launch the entire container network (FastAPI on 8000, React Nginx on 3000) with a single command:

```bash
# Build and run containers
docker-compose up --build
```
Navigate to [http://localhost:3000](http://localhost:3000) to view the application.

---

## 🧪 Running Automated Tests

We use `pytest` for server unit and integration checks.

```bash
# Activate backend virtual environment
cd backend
source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows

# Execute tests from project root
cd ..
pytest
```

---

## 🔒 Safety & Privacy Principles
1.  **Strictly Non-Clinical:** MindTrace does not make clinical psychiatric diagnoses. Do not edit user-facing texts to mention DSM conditions.
2.  **No Raw Logs:** Raw journal strings must *never* be printed to terminal logs, console errors, or diagnostic trackers.
3.  **Local Scrubbing:** Text is preprocessed to remove phone numbers, email addresses, and names prior to vector analysis.
