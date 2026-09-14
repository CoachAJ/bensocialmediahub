# 📋 Pharmacist Ben Social Media Hub: Master Setup & Credentials Checklist

This document is your step-by-step guide detailing **every item you need to provide**, **how to get it**, and **where to put it** across your 3 environments:
1. **Local Machine** (`.env` file)
2. **GitHub Actions Secrets** (Automated Daily Cloud Pipeline)
3. **Netlify Environment Variables** (Live Web Master Hub)

---

## 📑 Quick Summary Table

| Item Name | Variable Name | Required For | Where to Get It |
| :--- | :--- | :--- | :--- |
| **Gemini AI API Key** | `GEMINI_API_KEY` | Pipeline (AI Analysis & Hooks) | [Google AI Studio](https://aistudio.google.com) |
| **Buffer Access Token** | `BUFFER_ACCESS_TOKEN` | Buffer API (Dispatching posts) | [Buffer Developer Portal](https://buffer.com/developers) |
| **Buffer Profile IDs** | `BUFFER_PROFILE_IDS` | Buffer API (Target channels) | Buffer Dashboard / API |
| **Buffer Profile Mapping** | `BUFFER_PROFILE_MAP_JSON` | Channel routing (TikTok, IG, X) | Created from your profile IDs |
| **Google Service Account JSON** | `GDRIVE_SERVICE_ACCOUNT_JSON` | Google Drive & Sheets access | [Google Cloud Console](https://console.cloud.google.com) |
| **Drive Shorts Folder ID** | `GDRIVE_EXISTING_FOLDER_ID` | Ingesting pre-cut videos (<3m) | Google Drive Folder URL |
| **Google Sheet ID** | `GOOGLE_SHEET_ID` | Audit logging & metrics | Google Sheet URL |
| **Podcast RSS Feeds** | `RSS_BENS_BYTES`, etc. | Automated episode ingestion | Spotify/Libsyn/Buzzsprout RSS |
| **Health Coach Hotline** | `HEALTH_COACH_PHONE` | Social CTAs & Quiz embeds | `(855) 835-2777` (Configured) |
| **GitHub Access Token** | `GH_PAT` | Netlify 1-click cloud trigger | [GitHub Settings](https://github.com/settings/tokens) |

---

## 🛠️ Detailed Step-by-Step Instructions

### 1. Google Gemini API Key (`GEMINI_API_KEY`)
* **What it does**: Powers the multimodal video/audio analysis, timestamp extraction, hook writing, and Skool quiz generation.
* **How to get it**:
  1. Visit **[https://aistudio.google.com](https://aistudio.google.com)** and sign in with your Google account.
  2. Click **"Get API key"** in the top left.
  3. Click **"Create API key"** in a new or existing project.
  4. Copy the key (starts with `AIzaSy...`).
* **Where to put it**:
  * **Local**: In your `.env` file as: `GEMINI_API_KEY=AIzaSy...`
  * **GitHub**: Add secret named `GEMINI_API_KEY` at [https://github.com/CoachAJ/bensocialmediahub/settings/secrets/actions](https://github.com/CoachAJ/bensocialmediahub/settings/secrets/actions)

---

### 2. Buffer Access Token & Channel Profile IDs
* **What it does**: Schedules videos and platform-specific copy to your TikTok, Instagram Reels, and X channels within the Free Tier limits.

#### A. Buffer Access Token (`BUFFER_ACCESS_TOKEN`)
* **How to get it**:
  1. Log into your account at **[https://buffer.com](https://buffer.com)**.
  2. Go to the Developer Portal: **[https://buffer.com/developers/apps](https://buffer.com/developers/apps)**.
  3. Click **"Create an App"** (or use existing app).
  4. Name it `Ben Social Hub`. Redirect URL can be `https://buffer.com`.
  5. Once created, copy the **Personal Access Token** under "Access Token" (starts with `1/...`).
* **Where to put it**:
  * **Local**: In `.env` as: `BUFFER_ACCESS_TOKEN=1/...`
  * **GitHub**: Add secret named `BUFFER_ACCESS_TOKEN`
  * **Netlify**: Add variable named `BUFFER_ACCESS_TOKEN` in Netlify Site configuration (enables live queue gauges).

#### B. Buffer Profile IDs (`BUFFER_PROFILE_IDS` & `BUFFER_PROFILE_MAP_JSON`)
* **How to get it**:
  1. In Buffer's web app, click on your connected channel (e.g., your TikTok, Instagram, or X account).
  2. Look at the browser address bar:
     `https://publish.buffer.com/profile/65f1234567890abcdef12345/tab/queue`
  3. The alphanumeric string after `/profile/` (e.g., `65f1234567890abcdef12345`) is that channel's **Profile ID**.
  4. Note down the Profile ID for:
     * TikTok
     * Instagram
     * X (Twitter)
* **Where to put it**:
  * **Local & GitHub**:
    ```env
    BUFFER_PROFILE_IDS=id_tiktok,id_instagram,id_x
    BUFFER_PROFILE_MAP_JSON={"id_tiktok":"tiktok","id_instagram":"instagram","id_x":"x"}
    ```
  * **Netlify**: Add both `BUFFER_PROFILE_IDS` and `BUFFER_PROFILE_MAP_JSON` to Netlify environment variables.

---

### 3. Google Cloud Service Account (`GDRIVE_SERVICE_ACCOUNT_JSON`)
* **What it does**: Allows the serverless engine to automatically download files from your Google Drive, upload public video streaming links for Buffer, and append audit logs to Google Sheets.
* **How to get it**:
  1. Go to **[https://console.cloud.google.com](https://console.cloud.google.com)**.
  2. Create a new project (e.g., `Ben-Social-Hub`).
  3. Enable APIs: Go to **APIs & Services > Library**, search for and enable:
     * **Google Drive API**
     * **Google Sheets API**
  4. Create Service Account: Go to **IAM & Admin > Service Accounts** ➔ click **"Create Service Account"**.
     * Name: `ben-promo-bot` ➔ click **Create and Continue** ➔ click **Done**.
  5. Generate Key:
     * Click on the newly created service account email (e.g., `ben-promo-bot@ben-social-hub.iam.gserviceaccount.com`).
     * Click the **"Keys"** tab ➔ **"Add Key"** ➔ **"Create new key"** ➔ choose **JSON** ➔ click **Create**.
     * A `.json` file will download to your computer.
* **Where to put it**:
  * Open that `.json` file in a text editor (like Notepad), copy the **entire text**, and paste it as the value:
  * **Local**: In `.env` as: `GDRIVE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}`
  * **GitHub**: Add secret named `GDRIVE_SERVICE_ACCOUNT_JSON` with the raw JSON contents (or base64 encoded string).

> [!IMPORTANT]
> **Share your Google Drive folder and Google Sheet with the Service Account!**
> Copy the service account email (e.g. `ben-promo-bot@...iam.gserviceaccount.com`). In Google Drive and Google Sheets, click **Share**, paste that email, and grant **"Editor"** permission. Without this step, Google will block access!

---

### 4. Google Drive Folder IDs
* **What it does**: Tells the system where your pre-cut video shorts are stored.
* **How to get it**:
  1. Open Google Drive in your browser.
  2. Open the folder where you upload your short videos (<3 minutes).
  3. Look at the URL in your browser:
     `https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz_12345`
  4. The string after `/folders/` is your **Folder ID** (`1AbCdEfGhIjKlMnOpQrStUvWxYz_12345`).
* **Where to put it**:
  * **Local**: In `.env`:
    ```env
    GDRIVE_EXISTING_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz_12345
    ```
  * **GitHub**: Add secret named `GDRIVE_EXISTING_FOLDER_ID`.

---

### 5. Google Sheet ID (`GOOGLE_SHEET_ID`)
* **What it does**: Tracks every scheduled post, timestamp, channel, and Buffer ID in a spreadsheet for auditing.
* **How to get it**:
  1. Create a new Google Sheet (e.g. named `Pharmacist Ben Social Media Logs`).
  2. Look at the browser URL:
     `https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit`
  3. The string between `/d/` and `/edit` is your **Sheet ID** (`1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`).
  4. Remember to **Share** this sheet with your service account email as **Editor**.
* **Where to put it**:
  * **Local**: In `.env` as: `GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`
  * **GitHub**: Add secret named `GOOGLE_SHEET_ID`.

---

### 6. Podcast RSS Feed URLs
* **What it does**: The ingestion engine monitors these 3 feeds for new episodes to generate motion audiograms, waveforms, and Skool quizzes.
* **The 3 Variables**:
  * `RSS_BENS_BYTES`: RSS feed URL for *Pharmacist Ben's Bytes* (from Spotify for Podcasters, Anchor, etc.)
  * `RSS_MINERAL_WAY`: RSS feed URL for *The Mineral Way* (Libsyn RSS feed)
  * `RSS_AGING_WELL`: RSS feed URL for *The Art of Aging Well; Beauty, Body and Biology with Pharmacist Ben*
* **Where to put it**:
  * **Local**: In `.env`
  * **GitHub**: In Repository Secrets

---

### 7. GitHub Personal Access Token (`GH_PAT`)
* **What it does**: Allows your live **Netlify** Master Hub dashboard to remotely launch the GitHub Actions pipeline with 1 click when you tap "Run Pipeline Now".
* **How to get it**:
  1. Go to **[https://github.com/settings/tokens](https://github.com/settings/tokens)**.
  2. Click **"Generate new token"** ➔ **"Generate new token (classic)"**.
  3. Note: `Netlify Master Hub Dispatch`.
  4. Expiration: 90 days or No expiration.
  5. Check the **`repo`** checkbox and the **`workflow`** checkbox.
  6. Click **Generate token** and copy the string (starts with `ghp_...`).
* **Where to put it**:
  * **In Netlify**:
    1. Go to **[app.netlify.com](https://app.netlify.com)** ➔ Click your site.
    2. Go to **Site configuration > Environment variables**.
    3. Add a new variable:
       * Key: `GH_PAT`
       * Value: `ghp_your_token_here`

---

## 📍 Where to Place Each Variable

### 🏠 1. On Your Local Machine
Create or edit your local `.env` file in `c:\Users\atifj\OneDrive\Desktop\Ben social media Hub\.env`:

```env
# Google AI
GEMINI_API_KEY=AIzaSy...

# Buffer API
BUFFER_ACCESS_TOKEN=1/your_token_here
BUFFER_PROFILE_IDS=id_tiktok,id_instagram,id_x
BUFFER_PROFILE_MAP_JSON={"id_tiktok":"tiktok","id_instagram":"instagram","id_x":"x"}

# Google Cloud Service Account
GDRIVE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
GDRIVE_EXISTING_FOLDER_ID=your_drive_folder_id
GOOGLE_SHEET_ID=your_google_sheet_id

# Podcast RSS Feeds
RSS_BENS_BYTES=https://...
RSS_MINERAL_WAY=https://mineralway.libsyn.com/rss
RSS_AGING_WELL=https://...
```

---

### 🐙 2. In GitHub Repository Secrets
Go to: **[https://github.com/CoachAJ/bensocialmediahub/settings/secrets/actions](https://github.com/CoachAJ/bensocialmediahub/settings/secrets/actions)**  
Click **"New repository secret"** for each of these:

1. `GEMINI_API_KEY`
2. `BUFFER_ACCESS_TOKEN`
3. `BUFFER_PROFILE_IDS`
4. `BUFFER_PROFILE_MAP_JSON`
5. `GDRIVE_SERVICE_ACCOUNT_JSON`
6. `GDRIVE_EXISTING_FOLDER_ID`
7. `GOOGLE_SHEET_ID`
8. `RSS_BENS_BYTES`
9. `RSS_MINERAL_WAY`
10. `RSS_AGING_WELL`

---

### ⚡ 3. In Netlify Site Configuration
In your Netlify dashboard (**Site configuration > Environment variables**):

1. `GH_PAT` *(Enables 1-click cloud pipeline launch from the web dashboard)*
2. `BUFFER_ACCESS_TOKEN` *(Optional: Enables real-time queue gauges on Netlify)*
3. `BUFFER_PROFILE_MAP_JSON` *(Optional: Maps channel IDs for queue gauges)*
