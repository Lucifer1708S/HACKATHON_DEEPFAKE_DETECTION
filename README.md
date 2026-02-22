# 🛡️ HackHive: Deepfake Detector
**Real-time AI verification for images and videos.**

### 🌟 Project Overview
HackHive is a deep-learning tool designed to identify AI-generated media. By analyzing pixel-level artifacts, it can distinguish between a real human capture and an AI deepfake.

---

### 🚀 Key Features
* **Dual Support:** Analyzes both static images and video files.
* **Mobile Optimized:** Specifically handles rotation and compression artifacts from phone cameras.
* **Real-time Updates:** Uses a worker-queue system to show results instantly.

---

### 🔍 Analysis Scope (Current vs. Future)

| Feature | Status | Description |
| :--- | :--- | :--- |
| **Visual Analysis** | ✅ Available | Deep pixel-level scan for AI artifacts in images and video frames. |
| **Metadata Analysis** | ⚠️ In Progress | Basic EXIF data is read for orientation, but full structural metadata verification is coming soon. |
| **Audio Deepfake** | ❌ Not Available | Currently focuses on visual fakes; audio-based "voice clone" detection is a future update. |

---

### 🛠️ Tech Stack
* **Frontend:** React (Vite)
* **Database:** Supabase (Storage & Real-time Database)
* **AI Engine:** PyTorch & OpenCV
* **Neural Network:** EfficientNet-B0

---

### 📁 Project Structure
* `worker.py` – The script that listens for new uploads and manages tasks.
* `interference.py` – The AI logic that runs the deep learning model.
* `models/` – Folder containing the trained `.pth` weight files.
* `requirements.txt` – List of libraries needed to run the project.

---

### ⚙️ Quick Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt