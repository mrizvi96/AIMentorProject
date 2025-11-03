#!/bin/bash
# AI Mentor Service Manager
# Comprehensive script to manage all services (start, stop, status, restart)

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="/root/AIMentorProject"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_PATH="$BACKEND_DIR/venv"

# Service status functions
check_llm_server() {
    if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_backend_api() {
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_process_by_name() {
    local name=$1
    if ps aux | grep -v grep | grep "$name" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

get_gpu_info() {
    if command -v nvidia-smi &> /dev/null; then
        local gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        local gpu_mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
        echo "$gpu_name ($gpu_mem MB)"
    else
        echo "N/A"
    fi
}

# Status function
service_status() {
    echo "================================================"
    echo -e "${BLUE}AI Mentor Service Status${NC}"
    echo "================================================"
    echo ""

    # LLM Server
    echo -n "LLM Server (port 8080):     "
    if check_llm_server; then
        echo -e "${GREEN}✓ Running${NC}"
        model_name=$(curl -s http://localhost:8080/v1/models | python3 -c "import sys, json; print(json.load(sys.stdin)['data'][0]['id'])" 2>/dev/null || echo "unknown")
        echo "  Model: $model_name"
    else
        echo -e "${RED}✗ Not running${NC}"
    fi
    echo ""

    # Backend API
    echo -n "Backend API (port 8000):    "
    if check_backend_api; then
        echo -e "${GREEN}✓ Running${NC}"
        health=$(curl -s http://localhost:8000/ | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
        echo "  Health: $health"
    else
        echo -e "${RED}✗ Not running${NC}"
    fi
    echo ""

    # ChromaDB
    echo -n "ChromaDB (file-based):      "
    if [ -d "$BACKEND_DIR/chroma_db" ]; then
        db_size=$(du -sh "$BACKEND_DIR/chroma_db" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✓ Database exists ($db_size)${NC}"
    else
        echo -e "${YELLOW}⚠ Database not initialized${NC}"
    fi
    echo ""

    # GPU
    echo -n "GPU Status:                 "
    gpu_info=$(get_gpu_info)
    if [ "$gpu_info" != "N/A" ]; then
        echo -e "${GREEN}✓ $gpu_info${NC}"
    else
        echo -e "${RED}✗ No GPU detected${NC}"
    fi
    echo ""

    echo "================================================"
}

# Start services
start_services() {
    echo "================================================"
    echo -e "${BLUE}Starting AI Mentor Services${NC}"
    echo "================================================"
    echo ""

    # Check if already running
    if check_llm_server && check_backend_api; then
        echo -e "${YELLOW}⚠ Services already running${NC}"
        service_status
        exit 0
    fi

    # Activate virtual environment
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}✗ Virtual environment not found at $VENV_PATH${NC}"
        echo "  Run setup first: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi

    cd "$BACKEND_DIR"
    source "$VENV_PATH/bin/activate"

    # Start LLM Server
    if ! check_llm_server; then
        echo -e "${YELLOW}Starting LLM Server...${NC}"
        nohup python3 -m llama_cpp.server \
            --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
            --n_gpu_layers -1 \
            --n_ctx 4096 \
            --host 0.0.0.0 \
            --port 8080 \
            --chat_format mistral-instruct \
            --embedding true > llm_server.log 2>&1 &

        echo "  Waiting for model to load (30s)..."
        sleep 30

        if check_llm_server; then
            echo -e "${GREEN}✓ LLM Server started${NC}"
        else
            echo -e "${RED}✗ LLM Server failed to start. Check llm_server.log${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ LLM Server already running${NC}"
    fi
    echo ""

    # Start Backend API
    if ! check_backend_api; then
        echo -e "${YELLOW}Starting Backend API...${NC}"
        nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

        echo "  Waiting for API to initialize (5s)..."
        sleep 5

        if check_backend_api; then
            echo -e "${GREEN}✓ Backend API started${NC}"
        else
            echo -e "${RED}✗ Backend API failed to start. Check backend.log${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Backend API already running${NC}"
    fi
    echo ""

    echo -e "${GREEN}✅ All services started successfully${NC}"
    echo ""
    service_status
}

# Stop services
stop_services() {
    echo "================================================"
    echo -e "${BLUE}Stopping AI Mentor Services${NC}"
    echo "================================================"
    echo ""

    # Stop Backend API
    echo -n "Stopping Backend API...    "
    if pgrep -f "uvicorn main:app" > /dev/null; then
        pkill -f "uvicorn main:app"
        sleep 2
        echo -e "${GREEN}✓ Stopped${NC}"
    else
        echo -e "${YELLOW}⚠ Not running${NC}"
    fi

    # Stop LLM Server
    echo -n "Stopping LLM Server...     "
    if pgrep -f "llama_cpp.server" > /dev/null; then
        pkill -f "llama_cpp.server"
        sleep 2
        echo -e "${GREEN}✓ Stopped${NC}"
    else
        echo -e "${YELLOW}⚠ Not running${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Restart services
restart_services() {
    echo -e "${BLUE}Restarting services...${NC}"
    echo ""
    stop_services
    sleep 3
    start_services
}

# Show logs
show_logs() {
    local service=$1
    cd "$BACKEND_DIR"

    if [ "$service" = "llm" ]; then
        echo -e "${BLUE}LLM Server Logs (last 50 lines):${NC}"
        echo "================================================"
        tail -50 llm_server.log
    elif [ "$service" = "backend" ]; then
        echo -e "${BLUE}Backend API Logs (last 50 lines):${NC}"
        echo "================================================"
        tail -50 backend.log
    else
        echo -e "${RED}Unknown service: $service${NC}"
        echo "Usage: $0 logs [llm|backend]"
        exit 1
    fi
}

# Main command handler
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        service_status
        ;;
    logs)
        if [ -z "$2" ]; then
            echo "Usage: $0 logs [llm|backend]"
            exit 1
        fi
        show_logs "$2"
        ;;
    *)
        echo "AI Mentor Service Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - Show logs (usage: logs [llm|backend])"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 logs llm"
        exit 1
        ;;
esac
