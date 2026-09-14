# Pharmacist Ben Promotion Engine & Master Hub
# Comprehensive Operational Instructions & Playbook

Welcome to the comprehensive operational manual for **Pharmacist Ben's Autonomous Promotion Engine & Master Social Media Hub**. This document provides end-to-end, step-by-step instructions for running, operating, maintaining, and troubleshooting every aspect of the system.

---

## Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Operating Modes & Execution Environments](#2-operating-modes--execution-environments)
3. [Local PC Operation (No IDE Required)](#3-local-pc-operation-no-ide-required)
4. [Master Hub Command Center UI](#4-master-hub-command-center-ui)
5. [GitHub Actions 24/7 Cloud Automation](#5-github-actions-247-cloud-automation)
6. [Netlify Cloud Dashboard Management](#6-netlify-cloud-dashboard-management)
7. [Adding New Video Content to Google Drive](#7-adding-new-video-content-to-google-drive)
8. [Podcast RSS Feed Monitoring](#8-podcast-rss-feed-monitoring)
9. [Buffer Queue Strategy & Publishing Rules](#9-buffer-queue-strategy--publishing-rules)
10. [Google Sheets Live Audit Logging](#10-google-sheets-live-audit-logging)
11. [Troubleshooting & Maintenance Playbook](#11-troubleshooting--maintenance-playbook)

---

## 1. System Overview & Architecture

The Pharmacist Ben Promotion Engine is an autonomous multi-modal publishing pipeline designed for **"The Art of Aging Well: Beauty, Body and Biology with Pharmacist Ben"**.

### What It Does:
* **Ingests Raw Content**:
  * Pre-cut video shorts (<3 min) from Google Drive.
  * Audio episodes from 3 podcast RSS feeds (*The Mineral Way*, *Pharmacist Ben's Bytes*, *The Art of Aging Well*).
* **Analyzes with AI**: Uses **Google Gemini 3.6 Flash** to extract high-retention video hooks, clinical arguments, and platform-specific copy tailored to Pharmacist Ben's distinct voice.
* **Renders Vertical Assets**:
  * Slices and scales video to **9:16 vertical format** (1080x1920) with burned top hooks and bottom CTA banners.
  * Creates **9:16 vertical motion audiograms** with animated audio waveforms for podcast highlights.
* **Builds Community Quizzes**: Generates interactive HTML quiz embeds for the **Skool** student community.
* **Publishes to Social Media**: Directly queues posts with video assets into **Buffer** across **TikTok**, **Instagram Reels**, and **X (Twitter)**.
* **Logs Audits in Real Time**: Streams post timestamps, asset names, Buffer IDs, and status rows directly into a **Google Sheet** and local CSV file.
* **Conversion Target**: Every piece of content directs traffic to **`https://pharmacistbensacademy.com`** and displays the Certified Health Coach hotline: **`(855) 835-2777`**.

---

## 2. Operating Modes & Execution Environments

The system is engineered to run seamlessly across three distinct environments:

| Environment | Primary Purpose | How It Runs |
| :--- | :--- | :--- |
| **Local Windows PC** | Instant on-demand execution, local dashboard, offline testing | Python 3.12 CLI (`main.py`) & Local Server (`server.py`) |
| **GitHub Actions** | 100% automated 24/7 daily runs in the cloud (PC can be off) | Scheduled Ubuntu cron runner (`.github/workflows/pipeline.yml`) |
| **Netlify** | Web-accessible Master Hub dashboard from any device or phone | Static frontend (`dashboard/`) with Serverless Functions (`netlify/functions/`) |

---

## 3. Local PC Operation (No IDE Required)

You do not need any coding editor or IDE to run the engine. Your local `.env` file already contains all necessary API keys and settings.

### Opening the Project in Terminal:
1. Press `Windows Key + R`, type `powershell` (or `cmd`), and press **Enter**.
2. Navigate to your project folder:
   ```powershell
   cd "C:\Users\atifj\OneDrive\Desktop\Ben social media Hub"
   ```

### Execution Commands:

#### 1. Full Auto Run (Process both Drive shorts and Podcast drops):
```powershell
py -3.12 main.py --mode all
```
*Scans for new Google Drive shorts and new podcast episodes, processes up to 2 of each, renders videos, queues to Buffer, and logs to Google Sheets.*

#### 2. Process Drive Video Shorts Only:
```powershell
# Process 1 short:
py -3.12 main.py --mode shorts --max 1

# Process 3 shorts:
py -3.12 main.py --mode shorts --max 3
```

#### 3. Process Podcast Feeds Only:
```powershell
# Ingest latest podcast drop, generate audiogram & Skool quiz:
py -3.12 main.py --mode podcasts --max 1
```

#### 4. Dry Run / System Diagnostic Mode:
```powershell
py -3.12 main.py --mode dry-run
```
*Tests feeds, folder connections, and credentials without rendering video or consuming Buffer queue slots.*

---

## 4. Master Hub Command Center UI

The Master Hub is a browser-based dashboard providing real-time visual control.

### Starting the Local Dashboard:
```powershell
cd "C:\Users\atifj\OneDrive\Desktop\Ben social media Hub"
py -3.12 server.py
```
*The server will start on port `5000`.*

### Accessing the Dashboard:
Open your browser (Chrome, Edge, Safari, Firefox) and navigate to:
👉 **`http://localhost:5000`**

### Dashboard Features:
1. **Buffer Queue Gauges**: Live visual circular meters for TikTok, Instagram, and X showing queued posts (`X / 10`) and free slots.
2. **One-Click Run Button**: Click **"Run Engine Now"** to trigger the engine directly from your browser.
3. **Mode Selector**: Choose between `Full Auto Sync`, `Google Drive Shorts Only`, `Podcast Feeds Only`, or `Dry Run / Diagnostics`.
4. **Live Terminal Stream**: A real-time console window displaying pipeline stages (`[DRIVE]`, `[GEMINI]`, `[FFMPEG]`, `[BUFFER]`, `[SHEETS]`).
5. **Interactive Skool Quiz Preview**: Live preview card showing the generated interactive quiz module.
6. **Hotline & Branding Header**: Quick display of Pharmacist Ben's Academy link and coach hotline `(855) 835-2777`.

---

## 5. GitHub Actions 24/7 Cloud Automation

GitHub Actions acts as your automated robot in the cloud. It runs daily without needing your computer to be turned on.

### The Automated Schedule:
* **Workflow File**: `.github/workflows/pipeline.yml`
* **Trigger Time**: Daily at **12:00 UTC** (8:00 AM EST / 5:00 AM PST).

### What GitHub Actions Does During Each Run:
1. Boots an Ubuntu Linux virtual machine.
2. Sets up Python 3.11 and Node.js 20.
3. Installs system FFmpeg, DejaVu fonts, and project dependencies.
4. Executes `python main.py --mode all`.
5. Checks Google Drive folder and RSS feeds for new unprocessed content.
6. Cuts video, calls Gemini 3.6 Flash, and schedules posts to Buffer.
7. Dispatches live rows to your Google Sheet.
8. Commits the updated manifest (`data/processed.json`) and generated quiz embeds (`output/quizzes/`) back to GitHub so files are never processed twice.

### How to Trigger a Cloud Run Manually from GitHub:
1. Visit your repository: [https://github.com/CoachAJ/bensocialmediahub](https://github.com/CoachAJ/bensocialmediahub).
2. Click on the **Actions** tab at the top.
3. In the left sidebar, click **Pharmacist Ben Promotion Engine Pipeline**.
4. Click the **Run workflow** dropdown button (right side).
5. Select the mode (`all`, `shorts`, or `podcasts`) and click **Run workflow**.
6. Click the running workflow to watch real-time cloud terminal output.

---

## 6. Netlify Cloud Dashboard Management

Your Master Hub dashboard is configured for continuous deployment on Netlify.

### How It Works:
* **Config File**: `netlify.toml`
* **Build Directory**: `dashboard/`
* **Serverless Functions**: `netlify/functions/` (`stats.js`, `run.js`, `logs.js`).

### Viewing Your Netlify Dashboard:
1. Go to [Netlify Dashboard](https://app.netlify.com/).
2. Click on your site (**Ben Social Media Hub**).
3. Click the live site URL (`https://<your-site-name>.netlify.app`).

### Enabling 1-Click Cloud Triggers from Netlify:
To allow the **"Run Engine Now"** button on the public Netlify website to trigger your GitHub Actions runner:
1. Generate a GitHub Personal Access Token (classic) with `repo` scope at: [https://github.com/settings/tokens](https://github.com/settings/tokens).
2. In Netlify, go to **Site configuration > Environment variables**.
3. Add a variable named `GH_PAT` with your token value.
4. Now, clicking "Run Engine Now" on Netlify will trigger the GitHub cloud runner remotely.

---

## 7. Adding New Video Content to Google Drive

The engine continuously monitors your shared Google Drive shorts folder:
🔗 `https://drive.google.com/drive/folders/1OSrOtufSLN4DAFb1t9o8yPntzn3wdSdt?usp=sharing`

### Content Ingestion Protocol:
1. **Drop New MP4s**: Drop any raw short or edited video file (`.mp4`, `.mov`) directly into this Google Drive folder.
2. **File Naming Recommendation**: Use descriptive names (e.g. `Mitochondria and Cellular Energy.mp4`). This helps Gemini generate tightly focused hooks.
3. **Automatic Discovery**:
   - On the next run (local or cloud), the engine queries the folder metadata.
   - It compares each file against `data/processed.json`.
   - Any new file is downloaded, processed, scheduled, and recorded.
4. **Zero Re-posting Guarantee**: Once a video file ID is logged in `data/processed.json`, it is never scheduled again, avoiding duplicate posts.

---

## 8. Podcast RSS Feed Monitoring

The engine tracks three official podcast feeds:

1. **Pharmacist Ben's Bytes**:
   `https://anchor.fm/s/10c2c6674/podcast/rss`
2. **The Mineral Way**:
   `https://rss.libsyn.com/shows/562215/destinations/4859135.xml`
3. **The Art of Aging Well**:
   `https://bbsradio.com/customshow/mrss/290193` *(Awaiting upcoming episodes)*

### How Episodes Are Processed:
* Whenever a new episode is published to any of these feeds:
  1. The engine downloads a high-quality audio sample.
  2. Gemini 3.6 Flash identifies the most impactful 30–60 second clinical segment.
  3. FFmpeg generates a **9:16 vertical motion audiogram** with live animated waveforms.
  4. An interactive **Skool community quiz** is generated in `output/quizzes/` for student engagement.
  5. The post is queued to Buffer with dedicated links to `pharmacistbensacademy.com/podcasts`.

---

## 9. Buffer Queue Strategy & Publishing Rules

The engine is built around the **Buffer Free Tier** requirements:

### Buffer Account Profiles Connected:
* **TikTok**: Profile ID `6aa77842ea19ca0bde3b9a62` (`pharmacistbensacademy`)
* **Instagram Reels**: Profile ID `6aa77825ea19ca0bde3b9a1b` (`pharmacistbensacademy`)
* **X (Twitter)**: Profile ID `6aa77855ea19ca0bde3b9e83` (`BenFuchsAcademy`)

### Operational Rules:
1. **10-Post Queue Cap**: The engine automatically inspects your queue before posting. If a channel already has 10 scheduled posts, it skips dispatching to that channel until older posts are published, avoiding API rejections.
2. **Direct Video Attachments**: Buffer's GraphQL API requires direct streaming URLs in `assets: [{ video: { url: "..." } }]`. The engine passes high-speed direct download URLs from Google Drive so that all posts on TikTok, Instagram, and X contain the actual video file.
3. **Platform Tailored Copy**:
   - **TikTok**: High-impact curiosity hook + "link in bio" CTA.
   - **Instagram Reels**: Detailed educational breakdown + hashtags + "link in bio" CTA.
   - **X (Twitter)**: Punchy summary under 250 characters + direct clickable URL (`pharmacistbensacademy.com/podcasts`) + hotline `(855) 835-2777`.

---

## 10. Google Sheets Live Audit Logging

Every execution logs live rows directly to your Google Sheet:

### What Gets Logged:
| Column | Description | Example |
| :--- | :--- | :--- |
| **Timestamp** | ISO timestamp of the run | `2026-09-14 06:22:35 UTC` |
| **Asset Name** | Name of the video file or podcast episode | `American Life Cycle_ Cubicles...mp4` |
| **Asset Type** | Category of content | `Drive Short (Video)` or `Podcast Audiogram` |
| **Status** | Scheduling status | `Scheduled` |
| **Buffer Update ID** | Buffer transaction identifier | `6aa7920f490f0fc8d8b55112` |
| **CTA Destination** | Conversion target | `https://pharmacistbensacademy.com` |

### Where the Webhook Lives:
Your Google Apps Script Webhook is active at:
`https://script.google.com/macros/s/AKfycbz5FW7SYLjO4q9tMdUMYhW3kZgcWjbM8OCOaCg_HoWP-rVeK0O1x4hx2KkYqhwMkJPh/exec`

*If you ever create a new Google Sheet, simply paste the 8-line script from [SETUP_CHECKLIST.md](file:///c:/Users/atifj/OneDrive/Desktop/Ben%20social%20media%20Hub/SETUP_CHECKLIST.md#method-a-instant-google-sheets-webhook-recommended--no-google-cloud-keys-required) and update `GOOGLE_SHEET_WEBHOOK_URL` in `.env`.*

---

## 11. Troubleshooting & Maintenance Playbook

### Problem 1: "Buffer queue is full (10 posts)"
* **Cause**: Buffer Free plan allows 10 pending scheduled posts per profile.
* **Solution**: You don't have to do anything! The engine will automatically pause new dispatches to that channel. Once Buffer publishes older posts and creates free slots, the engine will resume scheduling automatically.

### Problem 2: "I added a new video to Google Drive, but it didn't schedule"
* **Check**:
  1. Open `data/processed.json`. Check if the filename or ID is listed under `existing_shorts`. If you want to force re-processing, remove that filename from `data/processed.json`.
  2. Verify that the file in Google Drive has permissions set to "Anyone with the link can view".

### Problem 3: "How do I clear the manifest to re-test from scratch?"
* Reset `data/processed.json` to an empty state:
  ```json
  {
    "existing_shorts": [],
    "podcast_episodes": []
  }
  ```

### Problem 4: "Port 5000 is already in use when running server.py"
* Another process or an earlier daemon is using port 5000.
* In PowerShell, run:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process -Force
  py -3.12 server.py
  ```

---

*Operational Playbook Version: 1.0.0 (Production)*  
*Maintained for Pharmacist Ben's Academy & The Art of Aging Well*
