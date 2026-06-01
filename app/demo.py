import time
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def parse_time(iso_str):
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

def run_demo():
    print("\n▶️ RUNNING RETRY ENGINE DEMO...\n")

    payloads = [
        {"id_name": "JOB 1: RECOVERY", "url": f"{BASE_URL}/mock-target", "method": "GET", "maxRetries": 5, "backoffMs": 1000},
        {"id_name": "JOB 2: TERMINAL 4xx", "url": "http://httpbin.org/status/404", "method": "GET", "maxRetries": 5, "backoffMs": 1000},
        {"id_name": "JOB 3: DEAD-LETTER", "url": "http://httpbin.org/status/503", "method": "GET", "maxRetries": 5, "backoffMs": 1000}
    ]

    # 1. Submit all jobs
    jobs = {}
    for p in payloads:
        res = requests.post(f"{BASE_URL}/request", json=p).json()
        jobs[res["id"]] = {"name": p["id_name"], "last_count": 0, "max_retries": p["maxRetries"]}
        print(f"📦 {p['id_name']} submitted.")

    print("\n" + "="*60 + "\n")
    
    # 2. Watch the worker process them live
    active_jobs = list(jobs.keys())
    while active_jobs:
        for req_id in active_jobs[:]:
            res = requests.get(f"{BASE_URL}/requests/{req_id}").json()
            status = res["status"]
            attempts = res.get("attempts", [])
            job_name = jobs[req_id]["name"]
            
            if len(attempts) > jobs[req_id]["last_count"]:
                latest = attempts[-1]
                att_num = latest['attemptNumber']
                
                # Clean up the error message for the visual log
                err_text = "Network Error"
                if latest['error']:
                    if "HTTP 404" in latest['error']: err_text = "404 Error"
                    elif "HTTP 503" in latest['error']: err_text = "503 Error"
                    elif "HTTP 500" in latest['error']: err_text = "500 Error"
                
                # Print the formatted attempt
                if status == "retrying":
                    wait = (parse_time(res['nextRetryAt']) - parse_time(latest['executedAt'])).total_seconds()
                    print(f"[{job_name}] ⏳ Attempt {att_num} ➔ {err_text} ➔ Retrying in ~{wait:.2f}s")
                
                elif status == "failed":
                    icon = "🛑" if "4xx" in job_name else "❌"
                    print(f"[{job_name}] {icon} Attempt {att_num} ➔ {err_text} ➔ FAILED")
                    if "4xx" in job_name:
                        print(f"   ↳ Rule Triggered: 4xx is terminal. Stopped instantly.\n")
                    else:
                        print(f"   ↳ Rule Triggered: Hit Max Retries (5). Dead-lettered.\n")
                        
                elif status == "completed":
                    print(f"[{job_name}] ✅ Attempt {att_num} ➔ 200 OK ➔ COMPLETED\n")
                
                jobs[req_id]["last_count"] = len(attempts)
                
            # Remove completed/failed jobs from the watch list
            if status in ["completed", "failed"]:
                active_jobs.remove(req_id)
                
        time.sleep(0.5)

    # 3. Print the Final Summary Report
    print("="*60)
    print("📊 DEMO SUMMARY REPORT")
    print("="*60)
    
    for req_id, job_info in jobs.items():
        res = requests.get(f"{BASE_URL}/requests/{req_id}").json()
        name = job_info["name"]
        status = res["status"].upper()
        
        attempts_taken = res.get("attemptCount", len(res.get("attempts", []))) 
        max_retries = job_info["max_retries"] 
        
        if status == "COMPLETED":
            icon = "✅"
            reason = "Successfully recovered"
        else:
            if "4xx" in name:
                icon = "🛑"
                reason = "Terminal Client Error"
            else:
                icon = "❌"
                reason = "Max Retries Reached"
                
        print(f"[{name}]")
        print(f"   ↳ ID      : {req_id}")
        print(f"   ↳ Status  : {icon} {status} ({reason})")
        print(f"   ↳ Attempts: {attempts_taken} / {max_retries}")
        print("-" * 60)

    print("🏁 DEMO FINISHED.\n")

if __name__ == "__main__":
    run_demo()