import subprocess
import sys
import time
import psutil
from pathlib import Path

# Setup shared log file for GUI live feed
LOG_FILE = Path(__file__).parent / "data" / "system.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_event(message):
    timestamp = time.strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def start_gui():
    log_event("Starting Streamlit Dashboard...")
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.headless=true"])

def start_scraper():
    log_event("Starting Extraction Daemon...")
    return subprocess.Popen([sys.executable, "src/flip_scraper.py"])

def check_memory(proc, name, limit_mb=1024):
    try:
        p = psutil.Process(proc.pid)
        mem_info = p.memory_info()
        mem_mb = mem_info.rss / (1024 * 1024)
        if mem_mb > limit_mb:
            log_event(f"WATCHDOG: {name} memory exceeded {limit_mb}MB ({mem_mb:.1f}MB). Restarting...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return True
    except psutil.NoSuchProcess:
        return True # Process died on its own
    return False

if __name__ == "__main__":
    # Clear log on startup
    with open(LOG_FILE, "w") as f:
        f.write("--- SYSTEM INITIALIZED ---\n")

    log_event("Initiating SLC Arbitrage Intelligence Station V3")

    gui_proc = start_gui()
    scrape_proc = start_scraper()

    last_scrape_time = time.time()
    SCRAPE_INTERVAL = 600 # 10 minutes

    try:
        while True:
            time.sleep(10)

            # Watchdog: GUI Memory
            if check_memory(gui_proc, "Streamlit GUI"):
                gui_proc = start_gui()

            # Watchdog: Scraper Memory / Status
            if scrape_proc.poll() is not None:
                # Scraper finished
                if time.time() - last_scrape_time > SCRAPE_INTERVAL:
                    scrape_proc = start_scraper()
                    last_scrape_time = time.time()
            else:
                # Scraper running, check memory
                if check_memory(scrape_proc, "Scraper Daemon"):
                    scrape_proc = start_scraper()
                    last_scrape_time = time.time()

    except KeyboardInterrupt:
        log_event("Shutting down infrastructure...")
        gui_proc.terminate()
        if scrape_proc.poll() is None:
            scrape_proc.terminate()
        sys.exit(0)
