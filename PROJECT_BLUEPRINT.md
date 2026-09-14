# Pharmacist Ben Social Media Hub & Promotion Engine
# Master Architecture Blueprint & Deep-Dive Specification

---

## Executive Summary

**Project Name**: Pharmacist Ben Promotion Engine & Master Control Hub  
**Brand**: "The Art of Aging Well: Beauty, Body and Biology with Pharmacist Ben"  
**Core Purpose**: Autonomous multi-modal ingestion, video/audio formatting, community gamification, and social media distribution engine driving qualified prospective students and supplement customers to **Pharmacist Ben's Academy**.  
**Primary CTA Destination**: `https://pharmacistbensacademy.com` (Podcasts archive and membership onboarding).  
**Dedicated Coaching & Product Hotline**: `(855) 835-2777` (Certified Health Coach inquiries & direct orders).  
**Repository**: `https://github.com/CoachAJ/bensocialmediahub.git`

---

## 1. Strategic Brand & Conversion Architecture

The software architecture is engineered to reinforce Pharmacist Ben's distinct clinical philosophy while methodically converting passive social media viewers into active Academy community members and coaching clients.

### 1.1 Clinical & Editorial Principles
1. **Holistic Biology over Symptom Management**: The system emphasizes that health is a biological process driven by cellular nutrition, digestive integrity, blood purification, and the 90 essential nutrients.
2. **Strict Compliance & Integrity**: The AI prompts strictly enforce a **zero miracle-cure** policy. No synthetic claims or "health in a bottle" promises are generated. Wellness is framed as biological mastery.
3. **Multi-Platform Conversion Tiers**:
   * **TikTok & Instagram Reels**: High-arousal curiosity hooks + educational summary + strong "link-in-bio" CTA directing viewers to the full podcast archive, with hotline guidance.
   * **X (Twitter)**: Dense, high-authority summaries under 250 characters + direct clickable URL (`https://pharmacistbensacademy.com/podcasts`) + coach hotline `(855) 835-2777`.
   * **Skool Community Quizzes**: Interactive educational widgets generated from podcast insights that test students, reinforce retention, and provide a direct enrollment gateway.

```
                  [ Raw Google Drive Shorts (<3m) ]       [ 3 Podcast RSS Feeds ]
                                  │                                  │
                                  ▼                                  ▼
                     [ Google Gemini 3.6 Flash ]         [ Audio Sample Ingestion ]
                    (Multimodal Clinical Engine)                     │
                                  │                                  ▼
         ┌────────────────────────┴────────────────────────┐ [ Gemini 3.6 Flash ]
         ▼                                                 ▼ (Nugget & Quiz Mining)
[ 9:16 Vertical Video Cutter ]                  [ 9:16 Vertical Audiogram ]  [ Skool Quiz HTML ]
(Burned Hooks & Academy CTA)                     (Dynamic Waveform Motion)    (Interactive Embed)
         │                                                 │
         └────────────────────────┬────────────────────────┘
                                  ▼
                     [ Buffer GraphQL API Engine ]
                     (@bufferapp/cli Stdin Pipe)
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
     [ TikTok ]           [ Instagram Reels ]          [ X / Twitter ]
 (Queue / Video Asset)    (Queue / Video Asset)    (Queue / Video Asset)
         │                        │                        │
         └────────────────────────┬────────────────────────┘
                                  ▼
                 [ Google Sheets Real-Time Audit ]
                   (Apps Script Webhook Stream)
```

---

## 2. Ingestion Subsystems

### 2.1 Track 1: Google Drive Shorts Ingestion (`src/drive_sync.py`)
* **Folder Link**: `https://drive.google.com/drive/folders/1OSrOtufSLN4DAFb1t9o8yPntzn3wdSdt?usp=sharing`
* **Zero-Credential Direct Download Bypass**: To eliminate dependency on Google Cloud Service Account JSON keys (often blocked by enterprise GCP organization policies), the engine utilizes an optimized `gdown` metadata crawler.
* **Remote Folder Crawling**:
  ```python
  remote_files = gdown.download_folder(url=folder_url, skip_download=True, quiet=True)
  ```
  This returns `GoogleDriveFileToDownload` objects containing each video's true alphanumeric Google Drive File ID (e.g. `1fGmsECmQHfPxC0G2khaYERLHZjrAGHfU`).
* **Direct Stream Construction**: The engine constructs high-speed direct download streaming URLs:
  `https://drive.google.com/uc?export=download&id=<FILE_ID>`
  These URLs allow Buffer's cloud transcoding service to download the video files directly.

### 2.2 Track 2: Podcast RSS Multi-Feed Ingestion (`src/rss_ingest.py`)
The engine dynamically tracks three RSS endpoints:
1. **Pharmacist Ben's Bytes**: `https://anchor.fm/s/10c2c6674/podcast/rss`
2. **The Mineral Way**: `https://rss.libsyn.com/shows/562215/destinations/4859135.xml`
3. **The Art of Aging Well**: `https://bbsradio.com/customshow/mrss/290193`

* **Parsing & Enclosure Resolution**: Uses `feedparser` to inspect `<enclosure>` and `<link>` nodes for `audio/mpeg` streams.
* **Streaming Audio Sampler**: Downloads the first 15 MB chunk (`download_podcast_audio_sample`) using chunked byte streaming, providing enough context for Gemini to extract golden nuggets without consuming unnecessary bandwidth.

---

## 3. Multimodal AI Processing Engine (`src/gemini_processor.py`)

The intelligence layer is powered by **Google Gemini 3.6 Flash** via the official `google-genai` SDK.

### 3.1 Pydantic Structured Output Schemas
The engine forces Gemini to return strict, type-validated JSON matching Pydantic data contracts:

```python
class ExistingShortCaptions(BaseModel):
    hook_headline: str          # Max 6 words, all-caps or high-impact title
    burned_cta_text: str        # e.g. "Full Archives @ PharmacistBensAcademy.com"
    caption_tiktok: str         # High curiosity hook + bio CTA
    caption_instagram: str      # Educational depth + relevant hashtags + bio CTA
    post_x: str                 # Punchy summary under 250 characters + link + phone
```

```python
class LongFormAnalysis(BaseModel):
    clips: list[ExtractedClip]  # Timestamps (MM:SS), hook headline, and copy
    quiz_question: str          # Multiple-choice question
    quiz_options: list[str]     # Exactly 4 options
    quiz_correct_index: int     # 0-3 index
    quiz_explanation: str       # Deep biological explanation
```

### 3.2 Automated Clinical Guardrails
System instructions embedded into every prompt enforce:
* Cellular nutrition & 90 essential nutrients framing.
* Addressing root-cause biology (digestive integrity, blood purification, mineral balance).
* Mandatory integration of the health coach phone hotline: `(855) 835-2777`.

---

## 4. Video & Audio Rendering Pipeline

### 4.1 9:16 Vertical Video Cutter (`src/video_cutter.py`)
Converts horizontal or variable-aspect raw clips into compliant 9:16 vertical shorts (1080x1920) for TikTok, Reels, and Shorts.

* **Aspect Ratio Transformation Filter**:
  ```text
  scale=1080:1920:force_original_aspect_ratio=decrease,
  pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black
  ```
* **Burned Top Hook Headline**:
  * Draws high-contrast yellow/white titles over a 50% opacity black bounding box.
  * Windows font fallback: `C\:/Windows/Fonts/arial.ttf` with fallback to Linux `DejaVuSans-Bold.ttf`.
  * Text escaping handles colons, commas, and single quotes to prevent FFmpeg filter graph syntax failures.
* **Burned Bottom CTA Banner**:
  * Permanently burns: `Full Archive @ PharmacistBensAcademy.com | Call (855) 835-2777` on the lower third.

### 4.2 Dynamic Motion Audiogram Generator (`src/audiogram_generator.py`)
Transforms raw podcast audio excerpts into 9:16 vertical video shorts:
* **Animated Waveform Generation**: Uses FFmpeg's `showwaves` filter:
  ```text
  showwaves=s=920x240:mode=line:colors=0x38bdf8@0.9:scale=cbrt
  ```
* **Visual Styling**:
  * Dark navy/slate background canvas (`#0b0f19`).
  * Upper show title banner with cyan accent.
  * Central quotation overlay highlighting Pharmacist Ben's core insight.
  * Live animated frequency waveform rendered in real time.
  * Bottom conversion footer with academy link and coach phone.

---

## 5. Gamification: Skool Community Quiz Engine (`src/skool_generator.py`)

To engage the **Skool** student body and generate lead capture, every podcast run generates an interactive, standalone HTML embed:

* **File Location**: `output/quizzes/<episode_id>_quiz.html`
* **Zero External Dependencies**: Pure Vanilla HTML5, CSS3, and JavaScript requiring no external libraries or build tools.
* **Interactive UI**:
  * Dark-mode theme styled with CSS custom properties.
  * 4 interactive option buttons.
  * Instant visual feedback (green for correct, red for incorrect with correct option highlighted).
  * Collapsible biological insight explanation box revealed upon answering.
  * Direct clickable CTA buttons to `pharmacistbensacademy.com` and clickable `tel:8558352777` hotline link.

---

## 6. Social Media Publishing Engine (`src/buffer_publisher.py`)

The social publishing subsystem is engineered around **Buffer's modern GraphQL API** and the official `@bufferapp/cli`.

### 6.1 Shift from Legacy REST to GraphQL
Buffer deprecated its legacy REST v1 API (`api.bufferapp.com/1/`) in favor of GraphQL (`api.buffer.com`). Modern Buffer API keys (beginning with alphanumeric tokens like `JGQHx4...`) authenticate via GraphQL Bearer tokens.

### 6.2 Stdin Pipe Architecture
To prevent Windows command shell (`cmd.exe`) syntax errors when escaping multi-line copy containing quotes, parentheses, and URLs, the engine passes JSON payloads via **stdin pipe**:
```bash
npx --yes @bufferapp/cli posts create --input - --output json
```
`subprocess.run(cmd, input=json.dumps(post_input), ...)` feeds the payload directly to the CLI's standard input.

### 6.3 Free Tier Safety Mechanisms
* **Queue Cap Inspection**: Before scheduling, the engine verifies that the profile's pending queue count is below the 10-post limit. If full, it logs a notice and skips dispatch until older posts publish.
* **Reels Metadata Injection**: For Instagram Reels, the payload automatically injects:
  ```json
  "metadata": {
    "instagram": {
      "type": "reel",
      "shouldShareToFeed": true
    }
  }
  ```
* **Draft Fallback Mechanism**: If a channel requires an asset not yet available, the engine automatically catches the API exception and saves the post as a **Draft** in the Buffer composer, ensuring no generated copy is ever lost.

---

## 7. Real-Time Audit & Data Persistence

### 7.1 State Manifest (`data/processed.json`)
Maintains an atomic state manifest tracking processed content:
```json
{
  "existing_shorts": [
    "American_Life_Cycle__Cubicles,_Salaries,_and_Healthcare_Costs.mp4",
    "Autoimmune_Diseases_Explained__From_Diabetes_to_Vitiligo.mp4"
  ],
  "podcast_episodes": [
    "1193344"
  ]
}
```
Prevents duplicate processing and ensures idempotency.

### 7.2 Google Apps Script Real-Time Webhook (`src/sheets_reporter.py`)
Whenever an asset is queued or drafted, an HTTP POST is dispatched to the Google Apps Script Webhook:
```javascript
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Timestamp", "Asset Name", "Asset Type", "Status", "Buffer Update ID", "CTA Destination"]);
  }
  sheet.appendRow([data.timestamp, data.asset_name, data.asset_type, data.status, data.buffer_update_id, data.cta_destination]);
  return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);
}
```
* Bypasses Google Cloud IAM and service account key restrictions.
* Appends rows in real time to the Google Sheet.
* Concurrently appends every event to `data/audit_log.csv` on local disk.

---

## 8. Deployment Topologies & Environments

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           DEPLOYMENT TOPOLOGY                           │
├───────────────────────────────────┬─────────────────────────────────────┤
│ LOCAL STANDALONE PC (Windows)     │ CLOUD RUNNER (GitHub Actions)       │
│ • Python 3.12 Runtime             │ • Ubuntu Linux Virtual Environment  │
│ • Local Server (http://localhost:5000)│ • Daily Cron at 12:00 UTC (8 AM EST)│
│ • Windows Subprocess Execution    │ • Headless FFmpeg & Node 20         │
│ • Reads local .env file           │ • Reads GitHub Actions Secrets      │
│ • Instant on-demand execution     │ • Automatic Git Manifest Commits    │
├───────────────────────────────────┴─────────────────────────────────────┤
│ NETLIFY WEB PLATFORM                                                    │
│ • Static Host for Command Center (dashboard/ -> publish)                │
│ • Serverless Functions (netlify/functions/)                             │
│ • Web UI for remote stats, queue gauges, and trigger dispatch           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Security & Anti-Leak Safeguards

* **`.gitignore` Enforcement**: Protects `.env`, `.env.*`, and `*.key` files from accidental commits.
* **GitHub Push Protection Compliance**: Secrets (Gemini keys, Buffer tokens, OAuth keys) are strictly isolated to `.env` and GitHub Secrets.
* **Public Asset Safety**: All video assets use Google Drive public direct download links or self-hosted delivery URLs, keeping credentials private.

---

*System Architecture Blueprint Version: 1.0.0 (Production Verified)*  
*Engineered for Pharmacist Ben Fuchs, Pharmacist Ben's Academy & The Art of Aging Well*
