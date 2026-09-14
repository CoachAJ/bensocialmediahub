import os
import sys
import json
import subprocess
import threading
from urllib.parse import urlparse, parse_qs
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 5000
DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "dashboard")

# Global runner state
CURRENT_RUN = {
    "status": "idle", # "idle", "running", "completed", "failed"
    "logs": [],
    "process": None
}
RUN_LOCK = threading.Lock()

class HubRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/stats":
            self.handle_api_stats()
        elif path == "/api/logs":
            self.handle_api_logs(parsed)
        else:
            # Fall back to serving static files from dashboard directory
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/run":
            self.handle_api_run()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_api_stats(self):
        # 1. Read manifest data
        manifest_path = os.path.join(os.path.dirname(__file__), "data", "processed.json")
        manifest_data = {"existing_shorts": [], "raw_media": [], "podcast_episodes": []}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except Exception:
                pass

        # 2. Count quizzes generated
        quiz_dir = os.path.join(os.path.dirname(__file__), "output", "quizzes")
        quiz_count = len(os.listdir(quiz_dir)) if os.path.exists(quiz_dir) else 0

        # 3. Buffer Queues (Try live query or default free slots)
        buffer_queues = {
            "tiktok": {"count": 2, "limit": 10},
            "instagram": {"count": 3, "limit": 10},
            "x": {"count": 1, "limit": 10}
        }
        
        try:
            from src.config import config
            from src.buffer_publisher import get_channel_queue_count
            mapping = config.get_profile_mapping()
            for pid, platform in mapping.items():
                if platform in buffer_queues:
                    count = get_channel_queue_count(pid)
                    buffer_queues[platform]["count"] = count
        except Exception:
            pass

        # 4. Service Health Checks
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        buffer_token = os.getenv("BUFFER_ACCESS_TOKEN", "")
        gdrive_creds = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "")

        response_payload = {
            "queues": buffer_queues,
            "manifest": {
                "existing_shorts": len(manifest_data.get("existing_shorts", [])),
                "podcast_episodes": len(manifest_data.get("podcast_episodes", [])),
                "quizzes": quiz_count
            },
            "health": {
                "gemini": bool(gemini_key),
                "buffer": bool(buffer_token),
                "drive": bool(gdrive_creds),
                "rss": True
            },
            "current_status": CURRENT_RUN["status"]
        }

        self.send_json(response_payload)

    def handle_api_logs(self, parsed):
        qs = parse_qs(parsed.query)
        since = int(qs.get("since", [0])[0])

        with RUN_LOCK:
            lines = CURRENT_RUN["logs"][since:]
            next_idx = len(CURRENT_RUN["logs"])
            status = CURRENT_RUN["status"]

        self.send_json({
            "lines": lines,
            "next_index": next_idx,
            "status": status
        })

    def handle_api_run(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        try:
            data = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            data = {}

        mode = data.get("mode", "all")

        with RUN_LOCK:
            if CURRENT_RUN["status"] == "running":
                self.send_json({"success": False, "error": "Pipeline is already executing."}, status=409)
                return

            CURRENT_RUN["status"] = "running"
            CURRENT_RUN["logs"] = [f"[SYSTEM] Pipeline launched in '{mode}' mode at {os.environ.get('USERNAME', 'admin')}@localhost"]

        # Run pipeline in a background thread
        thread = threading.Thread(target=self.execute_pipeline_process, args=(mode,), daemon=True)
        thread.start()

        self.send_json({"success": True, "mode": mode, "status": "running"})

    def execute_pipeline_process(self, mode: str):
        cmd = [sys.executable, "main.py", "--mode", mode]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(__file__)
            )
            with RUN_LOCK:
                CURRENT_RUN["process"] = process

            for line in iter(process.stdout.readline, ""):
                if line:
                    with RUN_LOCK:
                        CURRENT_RUN["logs"].append(line.rstrip())

            process.wait()
            with RUN_LOCK:
                if process.returncode == 0:
                    CURRENT_RUN["status"] = "completed"
                    CURRENT_RUN["logs"].append("[SYSTEM] Pipeline execution finished successfully.")
                else:
                    CURRENT_RUN["status"] = "failed"
                    CURRENT_RUN["logs"].append(f"[ERROR] Pipeline exited with code {process.returncode}.")
        except Exception as e:
            with RUN_LOCK:
                CURRENT_RUN["status"] = "failed"
                CURRENT_RUN["logs"].append(f"[FATAL] Process execution crashed: {e}")

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def start_server():
    server = HTTPServer(("127.0.0.1", PORT), HubRequestHandler)
    print(f"============================================================")
    print(f"  PHARMACIST BEN SOCIAL MEDIA HUB - COMMAND CENTER ACTIVE   ")
    print(f"  Access the dashboard at: http://localhost:{PORT}         ")
    print(f"  Funnel destination: https://pharmacistbensacademy.com     ")
    print(f"============================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Hub server.")

if __name__ == "__main__":
    start_server()
