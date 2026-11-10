#!/bin/bash
echo "Setting up DeepShield Enterprise Platform"
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r ml/requirements.txt
docker-compose up -d postgres redis
alembic upgrade head
echo "Setup complete. Run 'make docker' to start"
