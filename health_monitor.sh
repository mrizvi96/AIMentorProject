#!/bin/bash
# AI Mentor Health Monitor
# Continuous monitoring script with auto-restart capabilities

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_DIR="/root/AIMentorProject/backend"
CHECK_INTERVAL=60  # seconds
MAX_FAILURES=3

# Counters
llm_failures=0
backend_failures=0

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_and_restart_llm() {
    if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
        llm_failures=0
        return 0
    else
        ((llm_failures++))
        log_message "${RED}✗ LLM Server not responding (failure $llm_failures/$MAX_FAILURES)${NC}"

        if [ $llm_failures -ge $MAX_FAILURES ]; then
            log_message "${YELLOW}⚠ Attempting to restart LLM Server...${NC}"

            # Kill existing process
            pkill -f "llama_cpp.server" 2>/dev/null
            sleep 5

            # Restart
            cd "$BACKEND_DIR"
            source venv/bin/activate
            nohup python3 -m llama_cpp.server \
                --model ./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf \
                --n_gpu_layers -1 \
                --n_ctx 4096 \
                --host 0.0.0.0 \
                --port 8080 \
                --chat_format mistral-instruct \
                --embedding true >> llm_server.log 2>&1 &

            sleep 30

            if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
                log_message "${GREEN}✓ LLM Server restarted successfully${NC}"
                llm_failures=0
            else
                log_message "${RED}✗ Failed to restart LLM Server${NC}"
            fi
        fi
        return 1
    fi
}

check_and_restart_backend() {
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        backend_failures=0
        return 0
    else
        ((backend_failures++))
        log_message "${RED}✗ Backend API not responding (failure $backend_failures/$MAX_FAILURES)${NC}"

        if [ $backend_failures -ge $MAX_FAILURES ]; then
            log_message "${YELLOW}⚠ Attempting to restart Backend API...${NC}"

            # Kill existing process
            pkill -f "uvicorn main:app" 2>/dev/null
            sleep 3

            # Restart
            cd "$BACKEND_DIR"
            source venv/bin/activate
            nohup uvicorn main:app --host 0.0.0.0 --port 8000 >> backend.log 2>&1 &

            sleep 5

            if curl -s http://localhost:8000/ > /dev/null 2>&1; then
                log_message "${GREEN}✓ Backend API restarted successfully${NC}"
                backend_failures=0
            else
                log_message "${RED}✗ Failed to restart Backend API${NC}"
            fi
        fi
        return 1
    fi
}

check_gpu_health() {
    if ! command -v nvidia-smi &> /dev/null; then
        return 1
    fi

    # Check if GPU is accessible
    if ! nvidia-smi > /dev/null 2>&1; then
        log_message "${RED}✗ GPU not accessible${NC}"
        return 1
    fi

    # Check VRAM usage
    vram_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null)
    if [ "$vram_used" -lt 1000 ]; then
        log_message "${YELLOW}⚠ Low VRAM usage ($vram_used MB) - LLM may not be loaded${NC}"
    fi

    return 0
}

# Main monitoring loop
main() {
    log_message "${BLUE}Starting AI Mentor Health Monitor${NC}"
    log_message "Check interval: ${CHECK_INTERVAL}s"
    log_message "Max failures before restart: $MAX_FAILURES"
    log_message "Press Ctrl+C to stop"
    echo ""

    while true; do
        # Check LLM Server
        if check_and_restart_llm; then
            echo -ne "\r[$(date '+%H:%M:%S')] LLM: ${GREEN}✓${NC}  Backend: "
        else
            echo -ne "\r[$(date '+%H:%M:%S')] LLM: ${RED}✗${NC}  Backend: "
        fi

        # Check Backend API
        if check_and_restart_backend; then
            echo -ne "${GREEN}✓${NC}  GPU: "
        else
            echo -ne "${RED}✗${NC}  GPU: "
        fi

        # Check GPU
        if check_gpu_health; then
            vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null)
            echo -ne "${GREEN}✓${NC} (${vram}MB)    "
        else
            echo -ne "${RED}✗${NC}          "
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Handle script arguments
case "$1" in
    --once)
        # Run checks once and exit
        check_and_restart_llm
        llm_status=$?
        check_and_restart_backend
        backend_status=$?
        check_gpu_health
        gpu_status=$?

        if [ $llm_status -eq 0 ] && [ $backend_status -eq 0 ] && [ $gpu_status -eq 0 ]; then
            exit 0
        else
            exit 1
        fi
        ;;
    --help|-h)
        echo "AI Mentor Health Monitor"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --once    Run health check once and exit"
        echo "  --help    Show this help message"
        echo ""
        echo "Default: Run continuous monitoring"
        ;;
    *)
        main
        ;;
esac
