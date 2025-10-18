# 🔄 Fresh Runpod Instance - What's Saved vs. What to Download

## ✅ SAVED ON GITHUB (Just Clone!)

**Repository:** https://github.com/mrizvi96/AIMentorProject

All these files are **backed up and version controlled**:

### 📝 All Source Code (51 files)
```
✅ Backend Code:
   - main.py (FastAPI app)
   - chat_router.py (API endpoints)
   - config.py (configuration)
   - rag_service.py (RAG logic)
   - ingest.py (PDF ingestion script)
   - requirements.txt (Python dependencies)

✅ Frontend Code:
   - All Svelte components
   - API client (api.ts)
   - State management (stores.ts)
   - Main page (+page.svelte)
   - package.json (Node dependencies)

✅ Infrastructure:
   - docker-compose.yml (Milvus setup)
   - START_SERVICES.sh (automation)
   - start_llm_server.sh (LLM startup)
   - download_textbooks.sh (textbook downloader)

✅ Documentation (15+ files):
   - README.md
   - QUICKSTART.md
   - RUNPOD_DEPLOYMENT_CHECKLIST.md
   - SETUP_STATUS.md
   - UPLOAD_TEXTBOOKS_GUIDE.md
   - And many more...
```

**To get everything:**
```bash
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject
```

**That's it!** All code, scripts, and documentation are instantly available.

---

## ⬇️ NEED TO DOWNLOAD FRESH (Every New Instance)

These are **NOT in GitHub** and must be downloaded each time:

### 1. Mistral Model (4.8 GB) - 5-10 minutes
```bash
mkdir -p /workspace/models
wget -O /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"
```

**Why not in GitHub?**
- Too large (4.8GB > GitHub's file size limits)
- Changes rarely
- Available from HuggingFace
- Same file works across all instances

---

### 2. Your 6 Textbooks (153 MB) - 2-3 minutes
```bash
# Automated script (already in GitHub!)
./download_textbooks.sh
```

**Why not in GitHub?**
- Large binary files (153MB total)
- Could use Git LFS but adds complexity
- Google Drive links work perfectly
- Script makes it automatic anyway

**What the script downloads:**
- Textbook 1: 39 MB
- Textbook 2: 5.3 MB
- Textbook 3: 41 MB
- Textbook 4: 23 MB
- Textbook 5: 39 MB
- Textbook 6: 8.3 MB

---

### 3. Python Dependencies (~500 MB installed) - 3-5 minutes
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Why not in GitHub?**
- Generated files (can be recreated)
- Platform-specific binaries
- requirements.txt (the list) IS in GitHub
- pip installs automatically

---

### 4. Node Dependencies (~100 MB) - 1-2 minutes
```bash
cd frontend
npm install
```

**Why not in GitHub?**
- Generated files (node_modules/)
- Platform-specific
- package.json (the list) IS in GitHub
- npm installs automatically

---

### 5. Milvus Vector Database Data (Generated) - 5-10 minutes
```bash
# After textbooks are downloaded:
cd backend
source venv/bin/activate
python ingest.py --directory ../course_materials
```

**Why not in GitHub?**
- Generated from your textbooks
- Will be different each time you update PDFs
- Recreated via ingestion script
- Ingestion script IS in GitHub

---

## 📊 Complete Breakdown

| Item | Size | In GitHub? | Download Time | How to Get |
|------|------|------------|---------------|------------|
| **Source Code** | 1 MB | ✅ YES | 30 sec | `git clone` |
| **Documentation** | <1 MB | ✅ YES | 30 sec | `git clone` |
| **Scripts** | <1 MB | ✅ YES | 30 sec | `git clone` |
| **Mistral Model** | 4.8 GB | ❌ NO | 5-10 min | wget from HuggingFace |
| **6 Textbooks** | 153 MB | ❌ NO | 2-3 min | `./download_textbooks.sh` |
| **Python Deps** | ~500 MB | ❌ NO | 3-5 min | `pip install -r requirements.txt` |
| **Node Deps** | ~100 MB | ❌ NO | 1-2 min | `npm install` |
| **Milvus Data** | Varies | ❌ NO | 5-10 min | `python ingest.py` |

---

## ⏱️ Fresh Instance Timeline

### Total Time: **15-20 minutes**

**Step 1: Clone Repository** (30 seconds)
```bash
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject
```
✅ Gets all code, scripts, documentation

---

**Step 2: Download Model** (5-10 minutes) - **Can run in background**
```bash
mkdir -p /workspace/models
wget -O /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf" &
```

---

**Step 3: Download Textbooks** (2-3 minutes) - **Can run in background**
```bash
./download_textbooks.sh &
```

---

**Step 4: Install Python Dependencies** (3-5 minutes) - **Can run while downloads happen**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

---

**Step 5: Install Node Dependencies** (1-2 minutes)
```bash
cd frontend
npm install
cd ..
```

---

**Step 6: Start Milvus** (1-2 minutes)
```bash
systemctl start docker
docker-compose up -d
sleep 30  # Wait for healthy
```

---

**Step 7: Ingest Textbooks** (5-10 minutes)
```bash
cd backend
source venv/bin/activate
python ingest.py --directory ../course_materials
```

---

**Step 8: Start All Servers** (1-2 minutes)
```bash
# Terminal 1: LLM Server
./start_llm_server.sh

# Terminal 2: Backend
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd frontend
npm run dev -- --host 0.0.0.0
```

---

## 🎯 The KEY Point

### ✅ What You NEVER Have to Redo:
- Writing code (all in GitHub)
- Creating scripts (all in GitHub)
- Writing documentation (all in GitHub)
- Configuring project structure (all in GitHub)

### ⬇️ What You Download Fresh Each Time:
- Model file (one wget command)
- Textbooks (one script: `./download_textbooks.sh`)
- Dependencies (automatic: `pip install` and `npm install`)
- Vector database (automatic: `python ingest.py`)

---

## 💡 Why This Approach?

### GitHub Best Practices:
✅ **DO commit:** Source code, configuration, documentation, scripts
❌ **DON'T commit:** Large binaries, generated files, dependencies

### Our Approach:
✅ **In GitHub:** Everything you wrote/created
🤖 **Auto-download:** Everything that can be fetched/generated

### Result:
- **Clone once:** Get all your work
- **Download automated:** Scripts handle the rest
- **15-20 minutes:** Fresh instance to fully operational

---

## 🔐 Verification Checklist

After cloning, you should have:

```bash
# Check what's in GitHub
git ls-files | wc -l
# Should show: 51 files

# Check key files exist
ls -la backend/main.py                    # ✅
ls -la backend/app/services/rag_service.py # ✅
ls -la frontend/src/routes/+page.svelte   # ✅
ls -la docker-compose.yml                  # ✅
ls -la download_textbooks.sh               # ✅
ls -la RUNPOD_DEPLOYMENT_CHECKLIST.md     # ✅

# What's NOT there yet (will download):
ls -la /workspace/models/*.gguf            # ❌ (need to download)
ls -la course_materials/*.pdf              # ❌ (run download script)
ls -la backend/venv/                       # ❌ (run pip install)
ls -la frontend/node_modules/              # ❌ (run npm install)
```

---

## 🚀 Quick Reference Card

**Every new Runpod instance:**

```bash
# 1. Get all code/scripts (30 sec)
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject

# 2. Download model (5-10 min)
wget -O /workspace/models/Mistral-7B-Instruct-v0.2.Q5_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf"

# 3. Download textbooks (2-3 min)
./download_textbooks.sh

# 4. Follow RUNPOD_DEPLOYMENT_CHECKLIST.md
#    for remaining steps (setup + ingest + start)
```

**Total: 15-20 minutes to fully operational**

---

## ✅ Summary

**YES, everything you created is saved on GitHub:**
- ✅ All source code (backend + frontend)
- ✅ All configuration files
- ✅ All automation scripts
- ✅ All documentation
- ✅ Textbook download script with your Google Drive links

**What gets downloaded fresh (but automated):**
- Model (one wget command)
- Textbooks (one script)
- Dependencies (automatic installation)
- Vector data (automatic ingestion)

**You're completely safe!** Start a fresh Runpod instance anytime, clone from GitHub, and you'll have everything back in 15-20 minutes.

---

**Repository:** https://github.com/mrizvi96/AIMentorProject
**Status:** ✅ Complete backup, ready for deployment
