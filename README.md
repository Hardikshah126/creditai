# CreditAI 🏦

> AI-powered alternative credit scoring for India's 400M+ unbanked population

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Google Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)

---

## 🚀 What is CreditAI?

1.4 billion people globally have no credit score — not because they're bad with money, but because they never had a credit card.

**CreditAI solves this.** Upload your utility bills, rent receipts, or mobile recharge history. Our AI reads your documents, has a natural conversation with you, and generates a 0–100 credit score backed by a machine learning model — no bank account or credit card required.

---

## ✨ Features

- 📄 **Document Analysis** — Gemini AI extracts financial features from utility bills, rent receipts, UPI statements
- 🤖 **Conversational AI Agent** — Natural chat interface that fills data gaps through conversation
- 📊 **XGBoost Scoring** — ML model (ROC-AUC 0.93) scores users 0–100 with risk tier classification
- 🏦 **Lender Portal** — Role-based dashboard for lenders to view applicants, approve/reject
- 📑 **PDF Reports** — Downloadable credit reports with score breakdown and improvement areas
- 🇮🇳 **India-first** — All amounts in ₹ INR, context tailored for Indian financial documents
- 🔐 **JWT Auth** — Secure role-based access (applicant / lender)

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) **FastAPI** | REST API framework |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white) **PostgreSQL** | Primary database |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white) **SQLAlchemy** | Async ORM |
| ![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?style=flat&logo=python&logoColor=white) **XGBoost** | Credit scoring ML model (ROC-AUC 0.93) |
| ![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat&logo=google&logoColor=white) **Gemini 2.5 Flash** | Document extraction + conversational AI |
| ![ReportLab](https://img.shields.io/badge/ReportLab-CC0000?style=flat&logo=python&logoColor=white) **ReportLab** | PDF generation |

### Frontend
| Technology | Purpose |
|-----------|---------|
| ![React](https://img.shields.io/badge/React_18-61DAFB?style=flat&logo=react&logoColor=black) **React 18** | UI framework |
| ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white) **TypeScript** | Type safety |
| ![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white) **Vite** | Build tool |
| ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white) **Tailwind CSS** | Styling |
| ![shadcn/ui](https://img.shields.io/badge/shadcn/ui-000000?style=flat&logo=shadcnui&logoColor=white) **shadcn/ui** | Component library |

---

## 🏗️ Architecture

```
User uploads documents
        ↓
Gemini AI extracts financial features (utility streak, rent consistency, UPI volume)
        ↓
AI Agent asks natural follow-up questions (income, employment, dependents)
        ↓
XGBoost model scores 0-100 with risk tier (LOW / MEDIUM / HIGH)
        ↓
Gemini generates human-readable report narrative
        ↓
User shares report with lenders via lender portal
```

---

## 📁 Project Structure

```
creditai/
├── Backend/creditai-backend/
│   ├── app/
│   │   ├── api/routes/          # auth, agent, reports, lender, history, settings
│   │   ├── core/                # config, security, JWT
│   │   ├── db/                  # database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/
│   │       ├── agent_service.py     # Gemini conversation + feature extraction
│   │       ├── report_service.py    # PDF + report narrative
│   │       └── scoring_service.py   # XGBoost inference
│   └── ml/
│       ├── model.joblib             # Trained XGBoost model
│       └── train_model.py           # Training script
│
└── Frontend/credit-score-builder-main/
    └── src/
        ├── components/          # AppShell, ChatBubble, ScoreGauge, SignalCard
        ├── pages/               # Dashboard, Upload, Assistant, Report, Lender
        └── lib/api.ts           # Centralized API client
```

---

## ⚡ Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### Backend Setup

```bash
cd Backend/creditai-backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and GEMINI_API_KEY

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd Frontend/credit-score-builder-main

npm install
npm run dev
```

Open [http://localhost:8080](http://localhost:8080)

---

## 🔑 Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/creditai
SECRET_KEY=your-64-char-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080
GEMINI_API_KEY=your-gemini-api-key
UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=10
CORS_ORIGINS=http://localhost:8080
```

---

## 👤 Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Applicant | your@email.com | (register via signup) |
| Lender | hardik@lender.com | lender1234 |

---

## 📊 ML Model

The XGBoost model is trained on 12 alternative financial features:

| Feature | Source |
|---------|--------|
| `utility_payment_streak_months` | Document extraction |
| `utility_on_time_rate` | Document extraction |
| `avg_monthly_recharge_usd` | Document extraction |
| `recharge_consistency_score` | Document extraction |
| `rent_payment_consistency` | Document extraction |
| `upi_tx_frequency_per_month` | Document extraction |
| `avg_monthly_tx_volume_usd` | Document extraction |
| `income_stability_score` | AI conversation |
| `employment_type` | AI conversation |
| `num_dependents` | AI conversation |
| `had_informal_loan` | AI conversation |
| `data_completeness_score` | Calculated |

---

## 🤝 Contributing

This project is being built in public. Follow the journey on LinkedIn.


---

<p align="center">Built with ❤️ for India's unbanked population</p>
