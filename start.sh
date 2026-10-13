#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'
echo -e "${GREEN} Starting SOC telemetry Pipeline&Backend Serv...${NC}"

mkdir -p logs
echo -e "${CYAN}-> Starting Vector shipper...${NC}"
vector --config vector.toml & VECTOR_PID=$!

echo -e "${CYAN}-> Starting SOC Data Generator...${NC}"
source venv/bin/activate
python soc-generator/generator.py & GEN_PID=$!

echo -e "${CYAN}-> Starting Pipeline Health Poller...${NC}"
python poll_health.py & POLL_PID=$!

echo -e "${CYAN}-> Starting FastAPI backend (Uvicorn)...${NC}"
cd soc-backend
uvicorn app.main:app --reload --port 8000 & API_PID=$!
cd ..

echo -e "${GREEN} -- ALL SERVS UP AND RUNNING -- CTRL+C to stop${NC}"

trap "echo -e '\n${CYAN} Shutting down all services...${NC}'; kill $VECTOR_PID $GEN_PID $POLL_PID $API_PID 2>/dev/null; exit 0" SIGINT

wait
