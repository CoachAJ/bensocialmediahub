from src.config import config
from src.drive_sync import get_credentials

def log_event(
    timestamp: str,
    asset_name: str,
    asset_type: str,
    status: str,
    buffer_update_id: str,
    cta_destination: str = "pharmacistbensacademy.com"
):
    """
    Logs each processed and scheduled property to Google Sheets for performance tracking.
    """
    if not config.GOOGLE_SHEET_ID:
        print(f"[Sheets Logger - Dry Run] {timestamp} | {asset_name} | {asset_type} | {status} | Buffer ID: {buffer_update_id}")
        return

    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
        
        # Check if header exists; if sheet is empty, add header
        if len(sheet.get_all_values()) == 0:
            sheet.append_row(["Timestamp", "Asset Name", "Asset Type", "Status", "Buffer Update ID", "CTA Destination"])
            
        sheet.append_row([timestamp, asset_name, asset_type, status, buffer_update_id, cta_destination])
    except Exception as e:
        print(f"Warning: Failed to log event to Google Sheet {config.GOOGLE_SHEET_ID}: {e}")
