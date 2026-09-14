# 🧬 Pharmacist Ben's Social Media Hub & Promotion Engine

An automated, serverless promotional engine and interactive command center built to drive traffic to **[pharmacistbensacademy.com](https://pharmacistbensacademy.com)** (podcast archives & monthly Academy subscriptions) by distributing short-form motion video, GIFs, and platform-tailored copy across **TikTok, Instagram Reels, and X (Twitter)** via Buffer's Free Tier.

---

## 🌟 Key Features

1. **Strategic Conversion Funnel**: Every post hook, headline, and platform copy is engineered to direct viewers to the full episode archives at `pharmacistbensacademy.com/podcasts` and convert visitors into Academy members.
2. **Master Hub Web Interface**: A local browser-based command center (`http://localhost:5000`) with live Buffer queue gauges, manifest inventory counters, service health status, interactive Skool quiz previews, and one-click execution triggers.
3. **Dual-Track Content Ingestion**:
   - **Track 1: Existing Google Drive Shorts (<3 min)**: Slices 9:16 vertical video, burns top headline hooks and bottom CTA banners, and crafts platform copy.
   - **Track 2: Podcast RSS Feeds**: Ingests *Pharmacist Ben's Bytes*, *The Mineral Way*, and *The Art of Aging Well*, generating dynamic vertical audiograms/motion clips with animated audio waveforms.
4. **Buffer Free Tier Queue Protection**: Monitors pending queue limits (max 10 posts per channel) and routes platform-specific copy (TikTok, Instagram, and character-safe X copy).
5. **Interactive Skool Quizzes**: AI generates educational biological challenge quizzes and exports embeddable HTML cards for the Skool community.
6. **Automated Daily Runs**: Configured for GitHub Actions (`.github/workflows/pipeline.yml`) to run daily at 12:00 UTC with zero server hosting costs.

---

## 📁 Repository Structure

```text
podcast-promo-engine/
├── .github/
│   └── workflows/
│       └── pipeline.yml         # Daily automated GitHub Actions workflow
├── dashboard/
│   ├── index.html               # Master Hub Web Dashboard UI
│   ├── styles.css               # Modern dark-mode aesthetic styling
│   └── app.js                   # Dynamic stats polling & live log streaming
├── src/
│   ├── __init__.py
│   ├── config.py                # Environment configuration & credential decoders
│   ├── drive_sync.py            # Google Drive download & public clip upload
│   ├── gemini_processor.py      # Gemini 2.5 Flash multimodal analysis & CTAs
│   ├── video_cutter.py          # FFmpeg 9:16 vertical cutter with text escaping
│   ├── audiogram_generator.py   # Waveform motion video & GIF generator
│   ├── rss_ingest.py            # Parser for the 3 podcast RSS feeds
│   ├── buffer_publisher.py      # Buffer queue management & platform dispatch
│   ├── skool_generator.py       # Interactive Skool community HTML quiz builder
│   └── sheets_reporter.py       # Google Sheets event logger
├── templates/
│   └── quiz_template.html       # Standalone interactive quiz embed template
├── data/
│   └── processed.json           # Manifest tracking processed file IDs & GUIDs
├── main.py                      # CLI & pipeline orchestrator
├── server.py                    # Master Hub local web server (http://localhost:5000)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start (Local Master Hub)

### 1. Install Dependencies
```bash
py -3.12 -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

| Variable | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio key ([aistudio.google.com](https://aistudio.google.com)) |
| `BUFFER_ACCESS_TOKEN` | Buffer Developer Access Token ([buffer.com/developers](https://buffer.com/developers)) |
| `BUFFER_PROFILE_IDS` | Comma-separated channel IDs (TikTok, Instagram, X) |
| `GDRIVE_SERVICE_ACCOUNT_JSON` | Base64-encoded or raw JSON of Google Cloud Service Account |
| `GDRIVE_EXISTING_FOLDER_ID` | Drive folder ID with pre-cut short videos |
| `GOOGLE_SHEET_ID` | Google Sheet ID for audit logging |

### 3. Launch the Master Hub Web Interface
```bash
py -3.12 server.py
```
Open your browser to:
👉 **`http://localhost:5000`**

From the Master Hub, you can:
* Inspect your real-time **Buffer 10-slot queue gauges** for TikTok, Instagram, and X.
* Check **Drive shorts inventory** and **podcast episodes monitored**.
* Click **"Run Pipeline Now"** to trigger a full auto sync, shorts-only run, podcast run, or dry run with live terminal output.

---

## 🤖 Running via CLI

You can also run the orchestrator directly from your terminal:

```bash
# Full execution (Shorts + Podcasts)
py -3.12 main.py --mode all

# Process only uploaded Google Drive shorts
py -3.12 main.py --mode shorts

# Process only the 3 Podcast RSS Feeds
py -3.12 main.py --mode podcasts

# Dry run (test ingestion without external Buffer/Sheets writes)
py -3.12 main.py --mode dry-run
```

---

## ☁️ Deploying to GitHub Actions

1. Create a GitHub repository and push this codebase:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Pharmacist Ben Promotion Engine & Master Hub"
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
2. Navigate to **Settings > Secrets and variables > Actions** in your GitHub repository.
3. Add the secrets matching `.env.example`:
   - `GEMINI_API_KEY`
   - `BUFFER_ACCESS_TOKEN`
   - `BUFFER_PROFILE_IDS`
   - `BUFFER_PROFILE_MAP_JSON`
   - `GDRIVE_SERVICE_ACCOUNT_JSON`
   - `GDRIVE_EXISTING_FOLDER_ID`
   - `GDRIVE_RAW_FOLDER_ID`
   - `GDRIVE_OUTPUT_FOLDER_ID`
   - `GOOGLE_SHEET_ID`
   - `RSS_BENS_BYTES`
   - `RSS_MINERAL_WAY`
   - `RSS_AGING_WELL`
4. The workflow will run automatically daily at 12:00 UTC (8:00 AM EST) and can also be triggered manually under the **Actions** tab anytime!
