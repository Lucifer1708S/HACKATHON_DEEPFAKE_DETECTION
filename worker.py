import time
import os
from supabase import create_client
from interference import predict_media 

# --- CONFIGURATION ---
SUPABASE_URL = "https://koaxjoiphduqdcqiykly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvYXhqb2lwaGR1cWRjcWl5a2x5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTc2MDM1MiwiZXhwIjoyMDg3MzM2MzUyfQ.Hv9bl-ubKJJCPI8QEKQHrw9kWGK4-Ivvcj1bi-va2aw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "media-files" 

def process_queue():
    print("🚀 Worker Online | Listening to Supabase | Using RTX 3050")
    
    while True:
        try:
            # Fetch 1 pending job
            res = supabase.table("analyses").select("*, media_files(*)").eq("status", "pending").limit(1).execute()
            
            if res.data and len(res.data) > 0:
                job = res.data[0]
                job_id = job['id']
                media_data = job.get('media_files')
                
                if not media_data:
                    print(f"❌ Missing media for job {job_id}")
                    continue

                raw_path = media_data['storage_path']
                ext = os.path.splitext(raw_path)[1]
                local_file = f"temp_{job_id}{ext}"
                
                print(f"\n📥 New Task: {job_id} ({ext})")
                supabase.table("analyses").update({"status": "processing"}).eq("id", job_id).execute()

                # Robust Cloud Download
                data = None
                for p in [raw_path, raw_path.replace('media-files/', '', 1), raw_path.split('/')[-1]]:
                    try:
                        data = supabase.storage.from_(BUCKET_NAME).download(p)
                        if data: break
                    except: continue

                if not data:
                    print(f"❌ Failed to download {raw_path}")
                    supabase.table("analyses").update({"status": "failed"}).eq("id", job_id).execute()
                    continue

                # Execute AI
                try:
                    with open(local_file, "wb") as f:
                        f.write(data)
                    
                    is_auth, confidence = predict_media(local_file)
                    
                    supabase.table("analyses").update({
                        "status": "completed",
                        "is_authentic": is_auth,
                        "confidence_score": round(float(confidence) * 100, 2),
                        "completed_at": "now()"
                    }).eq("id", job_id).execute()

                    print(f"✅ Finished: {'AUTHENTIC' if is_auth else 'FAKE'} ({confidence*100:.2f}%)")
                
                except Exception as e:
                    print(f"❌ AI Error: {e}")
                    supabase.table("analyses").update({"status": "failed"}).eq("id", job_id).execute()
                
                finally:
                    if os.path.exists(local_file):
                        os.remove(local_file)
            
        except Exception as e:
            print(f"❌ System Loop Error: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    process_queue()