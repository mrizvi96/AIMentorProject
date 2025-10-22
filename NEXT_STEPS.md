# Next Steps: Runpod Custom Docker Image Deployment

## What We Just Created

I've set up everything you need to deploy AI Mentor on Runpod using a custom Docker image:

### Files Created:
1. **`Dockerfile`** - Custom image based on runpod/pytorch with all dependencies
2. **`.dockerignore`** - Optimizes build by excluding unnecessary files
3. **`start_all_services.sh`** - Automated script to start Milvus, LLM, and Backend
4. **`.github/workflows/docker-build.yml`** - GitHub Actions for automated Docker builds
5. **`RUNPOD_DOCKER_SETUP.md`** - Complete documentation for this approach

---

## Your Next Steps

### Step 1: Setup GitHub Secrets (5 minutes)

1. Go to **Docker Hub** (https://hub.docker.com)
   - Create account if you don't have one
   - Go to Account Settings → Security → New Access Token
   - Copy the token

2. Go to **Your GitHub Repository** → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add:
     - Name: `DOCKERHUB_USERNAME`, Value: your Docker Hub username
     - Name: `DOCKERHUB_TOKEN`, Value: the access token you just created

### Step 2: Commit and Push Code (2 minutes)

```bash
# From your local machine or current terminal
cd /root/AIMentorProject-1

# Add all new files
git add Dockerfile .dockerignore start_all_services.sh .github/ RUNPOD_DOCKER_SETUP.md NEXT_STEPS.md

# Commit
git commit -m "Add Runpod custom Docker image setup with automated builds"

# Push to GitHub
git push origin main
```

**What happens:** GitHub Actions will automatically build your Docker image and push it to Docker Hub!

### Step 3: Wait for Docker Build (10-15 minutes)

1. Go to your **GitHub repository** → Actions tab
2. Watch the "Build and Push Docker Image" workflow
3. When it's done, your image will be at: `YOUR_USERNAME/ai-mentor:latest`

### Step 4: Deploy on Runpod (5 minutes)

1. **Go to Runpod.io** → Click "Deploy"
2. **Select GPU**: RTX A5000 (24GB) or similar
3. **Template**: Select "Custom"
   - Docker Image Name: `YOUR_DOCKERHUB_USERNAME/ai-mentor:latest`
4. **Configure**:
   - Container Disk: 50GB
   - Volume Disk: 100GB (optional, for persistence)
   - Expose Ports: `8000,8080,19530,5173`
5. **Deploy**

### Step 5: Upload Mistral Model to Pod (10 minutes)

Once pod is running:

**Option A: Direct Download (if you have HuggingFace access)**
```bash
# SSH into pod
ssh root@YOUR_POD_IP -p PORT

cd /workspace/models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf
```

**Option B: Upload from Local Machine**
```bash
# From your local machine
scp -P PORT /path/to/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf root@YOUR_POD_IP:/workspace/models/
```

### Step 6: Start All Services (2 minutes)

```bash
# SSH into pod
ssh root@YOUR_POD_IP -p PORT

cd /workspace/AIMentorProject
./start_all_services.sh
```

This starts:
- ✅ Milvus vector database
- ✅ LLM server (llama.cpp)
- ✅ Backend FastAPI server

### Step 7: Ingest Course Materials (5-10 minutes)

```bash
cd /workspace/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials/
```

### Step 8: Test Everything (5 minutes)

```bash
# Test LLM Server
curl http://localhost:8080/v1/models

# Test Backend API
curl http://localhost:8000/

# Test Chat
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is Python?"}'
```

### Step 9: Access Frontend (from local machine)

The frontend should still be running from before. Update the API URL:

```typescript
// frontend/src/lib/api.ts
// Replace with your Runpod pod's public URL from dashboard
const API_BASE_URL = 'https://YOUR-POD-8000.runpod.io';
```

Then access: `http://localhost:5173`

---

## Quick Reference

### Useful Commands on Pod

```bash
# Check all services
docker-compose ps
tmux ls

# View logs
tmux attach -t llm      # LLM server logs
tmux attach -t backend  # Backend API logs
docker-compose logs -f  # Milvus logs

# Restart a service
tmux kill-session -t backend
tmux new-session -d -s backend "cd /workspace/AIMentorProject/backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# Stop everything
docker-compose down
tmux kill-server
```

### Service URLs (from Runpod Dashboard)

After deployment, check your Runpod dashboard for public URLs:
- Backend API: `https://YOUR-POD-8000.runpod.io`
- LLM Server: `https://YOUR-POD-8080.runpod.io`
- API Docs: `https://YOUR-POD-8000.runpod.io/docs`

---

## Timeline Summary

| Step | Time | What Happens |
|------|------|--------------|
| Setup GitHub Secrets | 5 min | One-time setup for Docker Hub |
| Commit & Push | 2 min | Trigger automated build |
| Docker Build | 10-15 min | GitHub Actions builds image |
| Deploy Runpod Pod | 5 min | Create pod with custom image |
| Upload Model | 10 min | Transfer 5GB model file |
| Start Services | 2 min | Run startup script |
| Ingest Data | 5-10 min | Load PDFs into Milvus |
| **Total** | **~40-50 min** | Complete deployment |

---

## Advantages of This Approach

✅ **Reproducible** - Same environment every time
✅ **Automated** - GitHub Actions builds on every push
✅ **Fast startup** - Pre-installed dependencies
✅ **No Docker-in-Docker issues** - Clean container setup
✅ **Version controlled** - Dockerfile in Git
✅ **Portable** - Works on any Runpod instance

---

## Troubleshooting

### GitHub Actions Build Fails

- Check you set `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets correctly
- Verify Docker Hub credentials are valid
- Check Actions tab for detailed error logs

### Docker Image Won't Pull on Runpod

- Make sure image is public on Docker Hub
- Or provide credentials in Runpod deployment settings
- Verify image name: `username/ai-mentor:latest` (all lowercase)

### Services Won't Start

```bash
# Check Docker daemon
systemctl status docker
systemctl start docker

# Check if ports are available
lsof -i :8000
lsof -i :8080
lsof -i :19530
```

---

## What's Next After This Works?

Once you have everything running:

1. ✅ **Test the frontend** - Verify full end-to-end chat works
2. ✅ **Phase 2: Implement Agentic RAG** - Add LangGraph workflow
3. ✅ **Phase 3: Add Testing** - pytest and CI/CD
4. ✅ **Phase 4: Evaluation** - Create test datasets

---

## Need Help?

Reference documents:
- **RUNPOD_DOCKER_SETUP.md** - Detailed setup guide
- **PHASE_1_COMPLETE.md** - Frontend completion summary
- **CLAUDE.md** - Project overview
- **SIX_WEEK_EXECUTION_PLAN.md** - Full development roadmap

---

**Current Status:**
- ✅ Frontend UI complete
- ✅ Backend API ready
- ✅ Docker image configured
- 🔄 Waiting for deployment to Runpod
- ⏳ Then: Start all services and test!
