import os
import csv
import requests
import gspread
from src.config import config

def log_event(
    timestamp: str,
    asset_name: str,
    asset_type: str,
    status: str,
    buffer_update_id: str,
    cta_destination: str = "pharmacistbensacademy.com"
):
    """
    Logs each processed property to:
    1. Local audit log CSV (data/audit_log.csv)
    2. Google Sheets Webhook (if GOOGLE_SHEET_WEBHOOK_URL is set)
    3. Google Sheets via gspread (if credentials exist)
    """
    # 1. Always record in local data/audit_log.csv
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "audit_log.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.exists(csv_path)
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Asset Name", "Asset Type", "Status", "Buffer Update ID", "CTA Destination"])
            writer.writerow([timestamp, asset_name, asset_type, status, buffer_update_id, cta_destination])
    except Exception as e:
        print(f"Notice: CSV log write error: {e}")

    # 2. Check for Google Sheets Webhook URL
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "")
    if webhook_url:
        try:
            requests.post(webhook_url, json={
                "timestamp": timestamp,
                "asset_name": asset_name,
                "asset_type": asset_type,
                "status": status,
                "buffer_update_id": buffer_update_id,
                "cta_destination": cta_destination
            }, timeout=10)
            return
        except Exception as e:
            print(f"Notice: Google Sheet webhook error: {e}")

    # 3. Check for Google Sheets via gspread API
    if not config.GOOGLE_SHEET_ID:
        print(f"[Sheets Logger] {timestamp} | {asset_name} | {asset_type} | {status} | Buffer ID: {buffer_update_id}")
        return

    try:
        from src.drive_sync import get_credentials
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
        if len(sheet.get_all_values()) == 0:
            sheet.append_row(["Timestamp", "Asset Name", "Asset Type", "Status", "Buffer Update ID", "CTA Destination"])
        sheet.append_row([timestamp, asset_name, asset_type, status, buffer_update_id, cta_destination])
    except Exception as e:
        print(f"Notice: Google Sheet API log note: {e}")
