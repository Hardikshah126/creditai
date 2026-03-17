#!/bin/bash
# CreditAI Backend — one-shot setup script
# Run from the /backend directory: bash setup.sh

set -e

echo "╔══════════════════════════════════════════╗"
echo "║      CreditAI Backend Setup              ║"
echo "╚══════════════════════════════════════════╝"

# 1. Python virtual environment
echo ""
echo "▶ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo ""
echo "▶ Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✓ Dependencies installed"

# 3. Copy .env if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  ✓ Created .env from .env.example"
  echo "  ⚠  Edit .env and set your ANTHROPIC_API_KEY and DATABASE_URL before running"
else
  echo "  ✓ .env already exists"
fi

# 4. Create upload directory
mkdir -p uploads
echo "  ✓ Created uploads/ directory"

# 5. Train ML model
echo ""
echo "▶ Training ML model (this takes ~30 seconds)..."
python ml/train_model.py
echo "  ✓ Model trained and saved to ml/credit_model.joblib"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Setup complete! Next steps:             ║"
echo "║                                          ║"
echo "║  1. Edit .env with your settings         ║"
echo "║  2. Start Postgres and create DB:        ║"
echo "║     createdb creditai_db                 ║"
echo "║  3. Run migrations:                      ║"
echo "║     alembic upgrade head                 ║"
echo "║  4. Start the server:                    ║"
echo "║     uvicorn app.main:app --reload        ║"
echo "║                                          ║"
echo "║  API docs: http://localhost:8000/docs    ║"
echo "╚══════════════════════════════════════════╝"
