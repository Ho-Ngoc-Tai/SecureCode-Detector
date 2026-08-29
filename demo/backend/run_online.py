import subprocess
import threading
import time
import re
import webbrowser
import os
import sys

def start_server():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="warning")

def main():
    print("=" * 65)
    print("        DEFECT-SCANNER AI - MASTER'S THESIS DEMO SERVER")
    print("=" * 65)
    print("\n[1/3] Khoi dong AI Server ngam (Port 8000)...")
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(3)

    print("[2/3] Dang khoi tao Duong truyen Public Cloudflare Tunnel...")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cloudflared_path = os.path.join(root_dir, "cloudflared.exe")
    
    if not os.path.exists(cloudflared_path):
        cloudflared_path = "cloudflared"
        
    cmd = [cloudflared_path, "tunnel", "--url", "http://127.0.0.1:8000"]
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
    except Exception as e:
        print(f"\nKhong tim thay cloudflared.exe ({e}). Chay tren Local: http://127.0.0.1:8000")
        webbrowser.open("http://127.0.0.1:8000")
        while True:
            time.sleep(1)
        return

    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    for line in proc.stdout:
        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    print("\n" + "=" * 65)
    print("       HE THONG DEFECT-SCANNER DA ONLINE SAN SANG!")
    print("=" * 65)
    print(f"\n  >> LINK NOI BO (Local):   http://127.0.0.1:8000")
    if public_url:
        print(f"  >> LINK PUBLIC (Hoi Dong): {public_url}")
        print("\n  (Dung dien thoai hoac laptop khac truy cap vao Link Public tren)")
        webbrowser.open(public_url)
    else:
        print("\n  >> Dang mo Localhost...")
        webbrowser.open("http://127.0.0.1:8000")
        
    print("\n" + "=" * 65)
    print("Nhan Ctrl + C de dung he thong.\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nDang tat Server...")
        proc.terminate()

if __name__ == "__main__":
    main()
