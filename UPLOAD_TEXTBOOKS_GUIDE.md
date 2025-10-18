# 📚 Guide: Upload PDF Textbooks to AI Mentor

This guide shows you how to upload your computer science PDF textbooks from your local laptop to your Runpod instance.

## Prerequisites

- ✅ PDF textbooks downloaded on your laptop
- ✅ Runpod instance running
- ✅ SSH connection details from Runpod

---

## Method 1: VS Code Remote-SSH (Recommended - Easiest)

### Step 1: Install VS Code Remote-SSH Extension

1. Open **Visual Studio Code** on your laptop
2. Go to Extensions (Ctrl+Shift+X or Cmd+Shift+X)
3. Search for **"Remote - SSH"**
4. Click **Install** on the Microsoft extension

### Step 2: Connect to Runpod

1. In VS Code, press **Ctrl+Shift+P** (Cmd+Shift+P on Mac)
2. Type **"Remote-SSH: Connect to Host"**
3. Select **"Add New SSH Host"**
4. Enter your Runpod SSH connection:
   ```
   ssh root@YOUR_RUNPOD_IP_OR_HOST
   ```
   Example: `ssh root@123.45.67.89` or `ssh root@ssh.runpod.io -p 12345`

5. When prompted, select your SSH config file (usually `~/.ssh/config`)
6. Click **"Connect"** and enter your password/key when prompted
7. VS Code will reload and connect to Runpod

### Step 3: Navigate to Project Directory

1. In VS Code, go to **File > Open Folder**
2. Navigate to: `/root/AIMentorProject/course_materials`
3. Click **OK**

### Step 4: Upload PDFs (Drag & Drop!)

1. In VS Code Explorer (left sidebar), you'll see the `course_materials` folder
2. **Drag and drop** your PDF files from your laptop directly into the folder
3. Or right-click in the Explorer and select **"Upload"**
4. Wait for upload to complete (progress shown in bottom-right)

**That's it! Super easy with VS Code.**

---

## Method 2: SCP Command (Fast for Multiple Files)

### For Windows (PowerShell or Command Prompt)

```powershell
# Single file
scp "C:\Users\YourName\Documents\textbook1.pdf" root@YOUR_RUNPOD_IP:/root/AIMentorProject/course_materials/

# Multiple files
scp "C:\Users\YourName\Documents\*.pdf" root@YOUR_RUNPOD_IP:/root/AIMentorProject/course_materials/

# Specific files
scp "C:\Users\YourName\Documents\textbook1.pdf" "C:\Users\YourName\Documents\textbook2.pdf" root@YOUR_RUNPOD_IP:/root/AIMentorProject/course_materials/

# With SSH port (if Runpod uses non-standard port)
scp -P 12345 "C:\Users\YourName\Documents\textbook.pdf" root@ssh.runpod.io:/root/AIMentorProject/course_materials/
```

### For Mac/Linux (Terminal)

```bash
# Single file
scp ~/Documents/textbook1.pdf root@YOUR_RUNPOD_IP:/root/AIMentorProject/course_materials/

# Multiple files
scp ~/Documents/*.pdf root@YOUR_RUNPOD_IP:/root/AIMentorProject/course_materials/

# Entire directory
scp -r ~/Documents/CS_Textbooks/* root@YOUR_RUNPOD_IP:/root/AIMentorProject/course_materials/

# With SSH port
scp -P 12345 ~/Documents/textbook.pdf root@ssh.runpod.io:/root/AIMentorProject/course_materials/
```

---

## Method 3: SFTP (GUI for Windows)

### Using WinSCP (Windows)

1. **Download WinSCP:** https://winscp.net/eng/download.php
2. **Install and open WinSCP**
3. **Enter connection details:**
   - File protocol: **SFTP**
   - Host name: Your Runpod IP
   - Port: 22 (or custom port from Runpod)
   - User name: **root**
   - Password: Your Runpod password
4. Click **Login**
5. Navigate to `/root/AIMentorProject/course_materials/`
6. **Drag and drop** PDFs from left (your laptop) to right (Runpod)

### Using FileZilla (Cross-platform)

1. **Download FileZilla:** https://filezilla-project.org/
2. **Install and open FileZilla**
3. **Enter at the top:**
   - Host: `sftp://YOUR_RUNPOD_IP`
   - Username: `root`
   - Password: Your password
   - Port: `22`
4. Click **Quickconnect**
5. Navigate to `/root/AIMentorProject/course_materials/`
6. **Drag and drop** PDFs from left to right

---

## Method 4: GitHub (For Persistent Storage)

If you want to version-control your textbooks with the project:

### Option A: Regular Git (Small PDFs < 50MB each)

```bash
# On your laptop, in your local project clone
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject

# Add PDFs
cp ~/Documents/*.pdf course_materials/

# Commit and push
git add course_materials/*.pdf
git commit -m "Add computer science textbooks"
git push origin main

# On Runpod, pull the changes
cd /root/AIMentorProject
git pull origin main
```

### Option B: Git LFS (Large PDFs > 50MB)

```bash
# On your laptop
git clone https://github.com/mrizvi96/AIMentorProject.git
cd AIMentorProject

# Install Git LFS
git lfs install

# Track PDF files
git lfs track "*.pdf"
git add .gitattributes

# Add your PDFs
cp ~/Documents/*.pdf course_materials/
git add course_materials/*.pdf
git commit -m "Add textbooks via Git LFS"
git push origin main

# On Runpod
cd /root/AIMentorProject
git lfs pull
```

**Note:** Git LFS has storage limits on free GitHub accounts.

---

## 📝 Getting Your Runpod Connection Info

### From Runpod Dashboard:

1. Go to https://www.runpod.io/console/pods
2. Find your running pod
3. Click **"Connect"**
4. You'll see connection options:

**SSH Connection Example:**
```
ssh root@123.45.67.89 -p 22
# Or
ssh root@ssh.runpod.io -p 12345
```

**Important Info:**
- **Host:** The IP address or hostname
- **Port:** Usually 22, but may be custom (like 12345)
- **Username:** Always `root`
- **Password:** Set when you created the pod (or use SSH key)

---

## ✅ Step-by-Step: Recommended Workflow

### 1. Connect via VS Code Remote-SSH

```
Host: YOUR_RUNPOD_IP
User: root
Password: YOUR_PASSWORD
```

### 2. Open Project Folder

```
/root/AIMentorProject/course_materials
```

### 3. Upload PDFs

- Drag and drop your textbooks
- Or right-click > Upload

### 4. Verify Upload

In VS Code terminal (or SSH):

```bash
cd /root/AIMentorProject
ls -lh course_materials/
```

You should see your PDFs listed with file sizes.

### 5. Run Ingestion

```bash
cd /root/AIMentorProject/backend
source venv/bin/activate
python ingest.py --directory ../course_materials
```

Watch the progress:
```
Loading documents from ../course_materials...
Found 5 PDF files
Loaded 5 documents
Created 247 chunks from 5 documents
Generating embeddings and storing in Milvus...
Progress: 10/247 chunks processed
...
✓ Document ingestion complete!
```

---

## 📊 Recommended PDF Organization

```
course_materials/
├── data_structures_algorithms.pdf
├── operating_systems.pdf
├── computer_networks.pdf
├── database_systems.pdf
└── software_engineering.pdf
```

**Tips:**
- ✅ Use descriptive filenames (no spaces, use underscores)
- ✅ Keep PDFs under 100MB each if possible
- ✅ Total 5-20 textbooks works well
- ✅ Scholarly/academic PDFs work best

---

## 🐛 Troubleshooting

### "Permission denied" during upload

```bash
# On Runpod, ensure directory exists and has correct permissions
cd /root/AIMentorProject
mkdir -p course_materials
chmod 755 course_materials
```

### "Connection refused"

- Verify Runpod instance is running
- Check SSH port (may not be 22)
- Ensure firewall allows SSH

### Upload is very slow

- Use SCP with compression:
  ```bash
  scp -C yourfile.pdf root@RUNPOD_IP:/root/AIMentorProject/course_materials/
  ```
- Or compress first:
  ```bash
  tar -czf textbooks.tar.gz *.pdf
  scp textbooks.tar.gz root@RUNPOD_IP:/root/AIMentorProject/
  # On Runpod:
  tar -xzf textbooks.tar.gz -C course_materials/
  ```

### File path has spaces

Always use quotes:
```bash
scp "C:\Users\My Name\Documents\My Textbook.pdf" root@IP:/root/AIMentorProject/course_materials/
```

---

## 🚀 After Upload: Next Steps

### 1. Verify Files

```bash
cd /root/AIMentorProject
ls -lh course_materials/
```

### 2. Ingest into Milvus

```bash
cd backend
source venv/bin/activate
python ingest.py --directory ../course_materials
```

### 3. Test the System

Start the servers (if not already running):
```bash
# Terminal 1: LLM Server
./start_llm_server.sh

# Terminal 2: Backend
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Frontend
cd frontend
npm run dev -- --host 0.0.0.0
```

### 4. Ask Questions

Open http://localhost:5173 and try:
- "What topics are covered in the data structures textbook?"
- "Explain binary search trees"
- "What are the main sorting algorithms?"

---

## 💡 Pro Tips

1. **Name files descriptively:**
   - ✅ `introduction_to_algorithms_cormen.pdf`
   - ❌ `book1.pdf`

2. **Group by subject:**
   ```
   course_materials/
   ├── algorithms/
   ├── operating_systems/
   └── databases/
   ```
   Then ingest: `python ingest.py --directory ../course_materials --recursive`

3. **Test with one file first:**
   - Upload one small PDF
   - Run ingestion
   - Test queries
   - Then upload the rest

4. **Keep a local backup:**
   - Always keep originals on your laptop
   - Runpod storage is ephemeral

5. **Re-use across sessions:**
   - Consider storing PDFs in GitHub (with Git LFS)
   - Or use cloud storage and download each session

---

## 📋 Quick Reference

| Method | Speed | Ease | Best For |
|--------|-------|------|----------|
| **VS Code Remote-SSH** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | First-time users, interactive |
| **SCP Command** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Power users, scripting |
| **WinSCP/FileZilla** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Windows users, GUI preference |
| **Git/Git LFS** | ⭐⭐ | ⭐⭐ | Version control, persistence |

---

**Need more help?**
- Check QUICKSTART.md for full setup
- See SETUP_STATUS.md for troubleshooting
- Open a GitHub issue

**Ready to ingest?** Run the ingestion script after uploading!
