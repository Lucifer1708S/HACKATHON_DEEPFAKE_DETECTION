import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client
from interference import predict_media

# --- DUMMY SERVER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"HackHive AI Worker is ACTIVE!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- CONFIG ---
SUPABASE_URL = "https://koaxjoiphduqdcqiykly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvYXhqb2lwaGR1cWRjcWl5a2x5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTc2MDM1MiwiZXhwIjoyMDg3MzM2MzUyfQ.Hv9bl-ubKJJCPI8QEKQHrw9kWGK4-Ivvcj1bi-va2aw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_pending_analyses():
    try:
        query = supabase.table("analyses").select("*, media_files(*)").eq("status", "pending").limit(1).execute()
        if not query.data: return

        job = query.data[0]
        analysis_id = job.get('id')
        media_data = job.get('media_files')
        
        res = supabase.storage.from_("media-files").create_signed_url(media_data['storage_path'], 60)
        file_url = res.get('signedURL')

        print(f"🚀 Processing: {media_data.get('file_name')}...")
        supabase.table("analyses").update({"status": "processing"}).eq("id", analysis_id).execute()

        # Get AI Result
        is_fake_raw, ai_confidence = predict_media(file_url)
        
        # --- LOGIC SYNC ---
        if is_fake_raw and ai_confidence > 0.65:
            is_fake = True
            trust_score = (1.0 - ai_confidence) * 100  # Convert to 0-100 scale
            result_label = "DEEPFAKE"
        else:
            is_fake = False
            # If it's authentic, we want a high trust score (e.g., 78)
            trust_score = ai_confidence * 100
            result_label = "AUTHENTIC"

        # Ensure we don't send a zero
        trust_score = max(5, min(99, trust_score))

        print(f"🎉 Final Verdict: {result_label} | Trust Score: {trust_score:.2f}%")

        # --- THE FIX: Sending as an Integer ---
        # If your DB is set to 'int', 0.78 becomes 0. Sending 78 fixes that.
        supabase.table("analyses").update({
            "status": "completed",
            "confidence_score": int(trust_score), 
            "is_authentic": not is_fake,
            "is_manipulated": is_fake,
            "completed_at": "now()"
        }).eq("id", analysis_id).execute()
        
    except Exception as e:
        print(f"❌ Worker Error: {e}")
        if 'analysis_id' in locals():
            supabase.table("analyses").update({"status": "failed"}).eq("id", analysis_id).execute()

if __name__ == "__main__":
    print("🤖 HackHive Worker Monitoring...")
    while True:
        process_pending_analyses()
        time.sleep(5)