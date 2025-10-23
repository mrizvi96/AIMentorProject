# Docker Hub Automated Builds - Quick Setup Guide

## Overview

This guide provides streamlined instructions for setting up Docker Hub Automated Builds to create the AI Mentor custom image without local disk space constraints.

**Why Docker Hub Automated Builds?**
- ✅ Builds on Docker Hub's infrastructure (no local disk space needed)
- ✅ Free for public repositories
- ✅ Automatic builds triggered by GitHub pushes
- ✅ No GitHub Actions disk space limitations (~14GB)
- ✅ Handles large PyTorch-based images

**Time Estimate:** 15-20 minutes setup + 20-30 minutes build time (passive)

---

## Prerequisites

✅ GitHub repository: `https://github.com/mrizvi96/AIMentorProject`
✅ Docker Hub account: `mrizvi96`
✅ Dockerfile, .dockerignore, and all project files committed to main branch

---

## Step-by-Step Setup

### 1. Login to Docker Hub (2 minutes)

1. Go to: https://hub.docker.com
2. Login with username: `mrizvi96`
3. Verify you're on the dashboard

### 2. Create New Repository (3 minutes)

1. Click **"Repositories"** in top navigation
2. Click **"Create Repository"** button
3. Fill in repository details:
   - **Name:** `ai-mentor` (lowercase, no spaces)
   - **Description:** `AI Mentor - Agentic RAG system for CS education with Milvus, Mistral-7B, and FastAPI`
   - **Visibility:**
     - Choose **Public** (free, anyone can pull)
     - OR **Private** (requires Docker Hub Pro subscription)
4. Click **"Create"**

**Result:** Repository created at `docker.io/mrizvi96/ai-mentor`

### 3. Connect to GitHub (5 minutes)

1. In your new `ai-mentor` repository, click the **"Builds"** tab
2. Click **"Configure Automated Builds"**
3. Click **"Connect to GitHub"**
4. Authorize Docker Hub to access your GitHub account
   - Review permissions
   - Click **"Authorize docker"**
5. Select organization: `mrizvi96`
6. Select repository: `AIMentorProject`
7. Click **"Save"** or **"Select"**

### 4. Configure Build Rules (5 minutes)

1. On the build configuration page, set:
   - **Source Type:** Branch
   - **Source:** `main` (or `master` if that's your default branch)
   - **Docker Tag:** `latest`
   - **Dockerfile location:** `/Dockerfile` (path from repository root)
   - **Build Context:** `/` (repository root)
   - **Autobuild:** ON (toggle enabled)
   - **Build Caching:** ON (recommended for faster rebuilds)

2. Optional advanced settings:
   - **Build on Push:** ON (builds automatically on git push)
   - **Tag Regular Expression:** Leave empty for now

3. Click **"Save and Build"**

### 5. Monitor Build Progress (20-30 minutes - passive)

1. Click the **"Builds"** tab in your repository
2. You should see a build job with status **"Building"**
3. Click on the build to see live logs (optional)
4. ☕ **Take a break while it builds**
5. Build stages you'll see:
   - Pulling base image (`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`)
   - Running apt-get update and installing system dependencies
   - Copying project files
   - Creating Python venv and installing requirements
   - Installing llama-cpp-python with CUDA support
   - Final image tagging and push

6. Wait for status to change to: **"Success"** ✅ with green checkmark

**Expected Build Time:** 20-30 minutes (depending on Docker Hub's current load)

### 6. Verify Build Success (1 minute)

Once build completes:

1. Check the **"Tags"** tab
   - You should see: `latest` tag with a recent timestamp
2. Note the image size (should be ~15-20GB)
3. Copy the pull command: `docker pull mrizvi96/ai-mentor:latest`

**Expected Result:** Image available at `docker.io/mrizvi96/ai-mentor:latest`

---

## Troubleshooting

### Build Fails: Base Image Not Found

**Error:** `manifest for runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404 not found`

**Fix:**
1. Verify the base image tag exists on Docker Hub
2. Update `Dockerfile` line 1 with correct tag
3. Commit and push to trigger new build

### Build Fails: Context Size Too Large

**Error:** `context size exceeds limit`

**Fix:**
1. Check `.dockerignore` includes large directories:
   ```
   models/
   volumes/
   course_materials/**/*.pdf
   node_modules/
   ```
2. Commit and push updated `.dockerignore`

### Build Timeout

**Error:** Build exceeds time limit (usually 2 hours)

**Fix:**
1. Optimize Dockerfile to reduce layers
2. Remove unnecessary dependencies from `requirements.txt`
3. Consider using pre-built base images for some dependencies

### Build Succeeds but Image Too Large

**Warning:** Image >30GB may be slow to pull on Runpod

**Fix:**
1. Use multi-stage builds to reduce final image size
2. Remove build-time dependencies in final stage
3. Compress layers with `RUN` command chaining

---

## After Successful Build

### Option 1: Deploy to Runpod Immediately

Follow **Phase 2** of `NEXT_SESSION_PLAN.md`:

1. Go to https://runpod.io
2. Click **"Deploy"** → **"GPU Pod"**
3. Select GPU: RTX A5000 (24GB VRAM)
4. Template: Custom
5. Docker Image Name: `mrizvi96/ai-mentor:latest`
6. Expose TCP Ports: `8000,8080,19530,5173`
7. Expose HTTP Ports: `8000,8080,5173`
8. Container Disk: 50GB minimum
9. Deploy and wait for pod to start

### Option 2: Test Locally First (if you have Docker)

**Note:** This requires ~20GB disk space locally and won't have GPU acceleration.

```bash
# Pull the image
docker pull mrizvi96/ai-mentor:latest

# Run the container
docker run -it --rm \
  -p 8000:8000 \
  -p 8080:8080 \
  -p 19530:19530 \
  -p 5173:5173 \
  mrizvi96/ai-mentor:latest \
  /bin/bash

# Inside container, start services
cd /workspace/AIMentorProject
./start_all_services.sh
```

---

## Future Updates

### Automatic Rebuilds on Git Push

Once configured, every `git push` to the `main` branch will trigger a new Docker build automatically.

**Workflow:**
1. Make code changes locally
2. `git add .`
3. `git commit -m "Update XYZ"`
4. `git push origin main`
5. Docker Hub automatically builds new image (20-30 min)
6. Pull updated image on Runpod: `docker pull mrizvi96/ai-mentor:latest`

### Manual Rebuilds

To rebuild without code changes:
1. Go to Docker Hub → `ai-mentor` repository → **Builds** tab
2. Click **"Trigger"** button next to the build rule
3. Confirm rebuild

---

## Important Notes

- **First build takes longest** (20-30 min) - subsequent builds use layer caching
- **Public images** can be pulled by anyone without authentication
- **Private images** require `docker login` before pulling
- **Image size** is large (~15-20GB) - first pull on Runpod takes 5-10 minutes
- **Build logs** are publicly visible for public repositories

---

## Repository URLs

- **Docker Hub Repository:** https://hub.docker.com/r/mrizvi96/ai-mentor
- **GitHub Repository:** https://github.com/mrizvi96/AIMentorProject
- **Build Logs:** https://hub.docker.com/r/mrizvi96/ai-mentor/builds

---

## Next Steps After Build Completes

1. ✅ Verify image is available: `docker pull mrizvi96/ai-mentor:latest`
2. → Proceed to **NEXT_SESSION_PLAN.md Phase 2** - Deploy to Runpod
3. → Upload Mistral model to pod
4. → Start services and test end-to-end

---

## Cost Considerations

**Docker Hub Free Tier:**
- Unlimited public repositories
- 1 private repository
- Unlimited automated builds
- Unlimited pulls for public images
- 200 pulls/6 hours for private images

**Runpod Costs:**
- RTX A5000: ~$0.34/hour (On-Demand) or ~$0.17/hour (Spot)
- Storage: $0.10/GB/month for persistent volumes
- Estimate for development: $5-10/week with spot instances

---

## Summary

This setup eliminates the need for local disk space or GitHub Actions limitations. Docker Hub handles the heavy lifting of building the large PyTorch-based image, and you only pay for Runpod GPU time when actively developing/testing.

**Total Setup Time:** ~15-20 minutes active work
**Build Time:** 20-30 minutes passive waiting
**Result:** Reusable Docker image deployable to any Runpod instance in ~10 minutes
