import subprocess
import os
import signal
import sys
import threading
from typing import Optional, Dict, List

class BotManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
            cls._instance.process = None
            cls._instance.current_mode = None
            cls._instance.logs = []
            cls._instance.log_lock = threading.Lock()
        return cls._instance

    def _capture_output(self, pipe):
        for line in iter(pipe.readline, b''):
            decoded_line = line.decode('utf-8', errors='replace').strip()
            with self.log_lock:
                self.logs.append(decoded_line)
                # Keep only last 500 lines
                if len(self.logs) > 500:
                    self.logs.pop(0)
        pipe.close()

    def start_bot(self, mode: str) -> bool:
        if self.process and self.process.poll() is None:
            return False # Already running
            
        with self.log_lock:
            self.logs = [] # Clear old logs
            
        cmd = [sys.executable, "-m", "src.main"]
        
        if mode == "login":
            cmd.append("--login")
        elif mode == "run_now_dry":
            cmd.extend(["--run-now", "--real", "--dry-run"])
        elif mode == "run_now_real":
            cmd.extend(["--run-now", "--real"])
        elif mode == "schedule_dry":
            cmd.extend(["--schedule", "--real", "--dry-run"])
        elif mode == "schedule_real":
            cmd.extend(["--schedule", "--real"])
        elif mode == "test_alstone":
            cmd.extend(["--test-order", "ALSTONE", "--real"])
        else:
            return False
            
        # Run in a new process group so we can kill it properly later
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            preexec_fn=os.setsid if os.name != 'nt' else None,
            env=os.environ.copy(),
            bufsize=1,
            universal_newlines=False
        )
        
        # Start logging thread
        threading.Thread(target=self._capture_output, args=(self.process.stdout,), daemon=True).start()
        
        self.current_mode = mode
        return True

    def stop_bot(self) -> bool:
        if not self.process or self.process.poll() is not None:
            return False
            
        try:
            if os.name != 'nt':
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()
            self.process = None
            self.current_mode = None
            return True
        except Exception:
            return False

    def get_status(self) -> Dict:
        is_running = self.process is not None and self.process.poll() is None
        return {
            "is_running": is_running,
            "mode": self.current_mode if is_running else None,
            "pid": self.process.pid if is_running else None
        }

    def get_logs(self) -> List[str]:
        with self.log_lock:
            return list(self.logs)

bot_manager = BotManager()
