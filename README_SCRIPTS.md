# AI Mentor Service Management Scripts

Quick reference guide for the service management and evaluation scripts.

---

## Scripts Overview

| Script | Purpose | Location |
|--------|---------|----------|
| `service_manager.sh` | Start/stop/monitor all services | Project root |
| `health_monitor.sh` | Continuous health monitoring with auto-restart | Project root |
| `run_evaluation.py` | Run system evaluation against question bank | backend/evaluation/ |
| `analyze_results.py` | Analyze evaluation results and generate reports | backend/evaluation/ |

---

## service_manager.sh

Comprehensive service control for all AI Mentor components.

### Usage

```bash
./service_manager.sh {start|stop|restart|status|logs}
```

### Examples

```bash
# Start all services
./service_manager.sh start

# Check service status
./service_manager.sh status

# View LLM server logs
./service_manager.sh logs llm

# View backend API logs
./service_manager.sh logs backend

# Restart all services
./service_manager.sh restart

# Stop all services
./service_manager.sh stop
```

### What It Manages

- **LLM Server** (port 8080): Mistral-7B inference via llama.cpp
- **Backend API** (port 8000): FastAPI server with agentic RAG
- **ChromaDB**: File-based vector database (no separate process)

---

## health_monitor.sh

Continuous monitoring with automatic service recovery.

### Usage

```bash
# Continuous monitoring (runs in foreground)
./health_monitor.sh

# Single health check (exits after one check)
./health_monitor.sh --once

# Background monitoring (keeps running)
nohup ./health_monitor.sh > monitor.log 2>&1 &
```

### Features

- Checks services every 60 seconds
- Auto-restart after 3 consecutive failures
- Real-time status display
- GPU health monitoring

### Output Example

```
[09:30:15] LLM: ✓  Backend: ✓  GPU: ✓ (6206MB)
```

---

## run_evaluation.py

Automated evaluation runner that queries the RAG system with a question bank.

### Usage

```bash
cd backend/evaluation
source ../venv/bin/activate

# Direct mode (recommended)
python3 run_evaluation.py --mode direct

# HTTP mode (requires backend running)
python3 run_evaluation.py --mode http
```

### Output

Creates `results/evaluation_YYYYMMDD_HHMMSS.json` with:
- All questions and responses
- Retrieved source documents
- Empty scoring fields for manual evaluation

### Next Steps After Running

1. Edit the output JSON file
2. Fill in manual scores (see EVALUATION_GUIDE.md)
3. Run analyze_results.py to generate report

---

## analyze_results.py

Processes manually-scored evaluation results and generates reports.

### Usage

```bash
cd backend/evaluation
source ../venv/bin/activate

# Generate markdown report
python3 analyze_results.py results/evaluation_TIMESTAMP.json

# Save report to file
python3 analyze_results.py results/evaluation_TIMESTAMP.json --output report.md

# Output metrics as JSON
python3 analyze_results.py results/evaluation_TIMESTAMP.json --json
```

### Output Metrics

- Overall score (0-5)
- Individual metric scores
- Category performance breakdown
- Difficulty performance breakdown
- Hallucination rate
- Retrieval success rate
- Recommendations for improvement

### Example Report

```
# AI Mentor Evaluation Report

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Questions | 20 |
| Scored Responses | 20 |
| Overall Score | 4.2/5.0 |
| Hallucination Rate | 5.0% |
| Retrieval Success Rate | 95.0% |

...
```

---

## Common Workflows

### Daily Operations

```bash
# Morning: Start services
./service_manager.sh start

# Check everything is running
./service_manager.sh status

# (Optional) Start health monitor in background
nohup ./health_monitor.sh > monitor.log 2>&1 &

# End of day: Stop services (save GPU costs)
./service_manager.sh stop
```

### After Code Changes

```bash
# Restart services to pick up changes
./service_manager.sh restart

# Check logs for errors
./service_manager.sh logs backend
```

### Running Evaluation

```bash
# 1. Ensure services are running
./service_manager.sh status

# 2. Run evaluation
cd backend/evaluation
source ../venv/bin/activate
python3 run_evaluation.py --mode direct

# 3. Manual scoring
nano results/evaluation_*.json

# 4. Generate report
python3 analyze_results.py results/evaluation_*.json --output report.md
cat report.md
```

### Troubleshooting

```bash
# Check what's wrong
./service_manager.sh status

# View recent logs
./service_manager.sh logs llm | tail -50
./service_manager.sh logs backend | tail -50

# Restart everything
./service_manager.sh restart

# If still broken, check GPU
nvidia-smi

# Check if processes are stuck
ps aux | grep -E "llama_cpp|uvicorn"

# Force kill if needed
pkill -9 -f "llama_cpp.server"
pkill -9 -f "uvicorn"
```

---

## Script Locations

```
/root/AIMentorProject/
├── service_manager.sh           # Main service control
├── health_monitor.sh            # Health monitoring
├── backend/
│   ├── evaluation/
│   │   ├── run_evaluation.py   # Evaluation runner
│   │   ├── analyze_results.py  # Results analyzer
│   │   ├── question_bank.json  # Question bank
│   │   └── results/            # Evaluation outputs
│   ├── llm_server.log          # LLM server logs
│   └── backend.log             # Backend API logs
└── README_SCRIPTS.md           # This file
```

---

## Environment Requirements

All scripts assume:
- Working directory: `/root/AIMentorProject/`
- Backend venv: `backend/venv/`
- Python: 3.12+
- CUDA: Available and working

---

## Exit Codes

All scripts follow standard exit codes:
- `0`: Success
- `1`: Error or service down
- `2`: Invalid arguments

Use in scripts:
```bash
./service_manager.sh status
if [ $? -eq 0 ]; then
    echo "All services running"
else
    echo "Some services down"
fi
```

---

## Logging

### Log Locations

- LLM Server: `backend/llm_server.log`
- Backend API: `backend/backend.log`
- Health Monitor: stdout (or redirect with `nohup`)

### Log Rotation

Logs can grow large. Rotate periodically:

```bash
# Backup and clear logs
cd backend
mv llm_server.log llm_server.log.$(date +%Y%m%d)
mv backend.log backend.log.$(date +%Y%m%d)
touch llm_server.log backend.log
```

---

## Integration with Cron

```bash
# Edit crontab
crontab -e

# Start services at boot
@reboot /root/AIMentorProject/service_manager.sh start

# Health check every hour
0 * * * * /root/AIMentorProject/health_monitor.sh --once

# Weekly evaluation (Sunday 2 AM)
0 2 * * 0 cd /root/AIMentorProject/backend/evaluation && /root/AIMentorProject/backend/venv/bin/python3 run_evaluation.py --mode direct

# Daily log cleanup (keep last 7 days)
0 3 * * * find /root/AIMentorProject/backend/*.log.* -mtime +7 -delete
```

---

## Quick Reference Card

```
SERVICE MANAGEMENT
──────────────────
Start:    ./service_manager.sh start
Stop:     ./service_manager.sh stop
Status:   ./service_manager.sh status
Restart:  ./service_manager.sh restart
Logs:     ./service_manager.sh logs {llm|backend}

HEALTH MONITORING
─────────────────
Monitor:  ./health_monitor.sh
Check:    ./health_monitor.sh --once

EVALUATION
──────────
Run:      cd backend/evaluation && python3 run_evaluation.py
Analyze:  python3 analyze_results.py results/FILE.json

DEBUGGING
─────────
GPU:      nvidia-smi
Procs:    ps aux | grep -E "llama|uvicorn"
Ports:    lsof -i :8080 && lsof -i :8000
```

---

For detailed guides, see:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Full deployment instructions
- [backend/evaluation/EVALUATION_GUIDE.md](backend/evaluation/EVALUATION_GUIDE.md) - Evaluation details
- [CLAUDE.md](CLAUDE.md) - Project overview and architecture
