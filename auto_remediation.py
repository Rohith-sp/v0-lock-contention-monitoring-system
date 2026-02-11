"""
Auto-Remediation System for Lock Contention
Automatically reduces contention when HIGH risk is detected
"""

import subprocess
import time
import os
import signal
from datetime import datetime

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'

class ContentionRemediator:
    """
    Automatically reduces contention when HIGH risk detected.
    
    Strategies:
    1. Throttle workload (add delays)
    2. Split workload into multiple processes
    3. Kill and restart with lower thread count
    """
    
    def __init__(self):
        self.remediation_log = []
        self.last_remediation_time = None
        self.cooldown_seconds = 30  # Don't remediate too frequently
    
    def can_remediate(self):
        """Check if enough time has passed since last remediation"""
        if self.last_remediation_time is None:
            return True
        
        elapsed = time.time() - self.last_remediation_time
        return elapsed > self.cooldown_seconds
    
    def log_action(self, action, details):
        """Log remediation action"""
        entry = {
            'timestamp': datetime.now(),
            'action': action,
            'details': details
        }
        self.remediation_log.append(entry)
        
        print(f"\n{Colors.CYAN}[REMEDIATION]{Colors.RESET} {action}")
        print(f"  Details: {details}")
        print(f"  Time: {entry['timestamp'].strftime('%H:%M:%S')}\n")
    
    def remediate_high_contention(self, risk_level, metrics, extra_threads):
        """
        Main remediation logic.
        
        Called when HIGH contention is detected.
        """
        if risk_level != 'HIGH':
            return False
        
        if not self.can_remediate():
            remaining = self.cooldown_seconds - (time.time() - self.last_remediation_time)
            print(f"{Colors.YELLOW}  Cooldown active ({remaining:.0f}s remaining){Colors.RESET}")
            return False
        
        print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}     HIGH CONTENTION DETECTED - INITIATING REMEDIATION{Colors.RESET}")
        print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
        
        # Strategy 1: Suggest splitting workload
        if extra_threads > 15:
            self.suggest_process_split(extra_threads)
        
        # Strategy 2: Recommend throttling
        self.suggest_throttling(metrics)
        
        # Strategy 3: Show how to reduce thread count
        self.suggest_thread_reduction(extra_threads)
        
        self.last_remediation_time = time.time()
        return True
    
    def suggest_process_split(self, extra_threads):
        """Suggest splitting workload into multiple processes"""
        suggested_processes = max(2, extra_threads // 8)  # ~8 threads per process
        
        self.log_action(
            "SUGGEST: Split into Multiple Processes",
            f"Current: 1 process with {extra_threads} threads → "
            f"Suggested: {suggested_processes} processes with ~8 threads each"
        )
        
        print(f"{Colors.BOLD}Why this helps:{Colors.RESET}")
        print(f"  • Multiple processes = separate memory spaces")
        print(f"  • No shared locks between processes")
        print(f"  • Better CPU utilization")
        print(f"  • Reduced lock contention\n")
        
        print(f"{Colors.BOLD}How to implement:{Colors.RESET}")
        print(f"  1. Stop current workload (Ctrl+C)")
        print(f"  2. Run: python contention_workload.py low  (in {suggested_processes} terminals)")
        print(f"  3. Each process has fewer threads = less contention\n")
    
    def suggest_throttling(self, metrics):
        """Suggest adding delays to reduce contention"""
        current_wait = metrics.get('avg_wait_time_ms', 0)
        
        self.log_action(
            "SUGGEST: Add Throttling",
            f"Current wait time: {current_wait:.0f}ms → Add delays between operations"
        )
        
        print(f"{Colors.BOLD}Why this helps:{Colors.RESET}")
        print(f"  • Delays reduce lock acquisition rate")
        print(f"  • Gives other threads time to complete")
        print(f"  • Spreads load over time\n")
        
        print(f"{Colors.BOLD}How to implement:{Colors.RESET}")
        print(f"  1. Stop current workload (Ctrl+C)")
        print(f"  2. Run: python contention_workload.py low  (lower intensity)")
        print(f"  3. Or modify workload to add time.sleep(0.01) between operations\n")
    
    def suggest_thread_reduction(self, extra_threads):
        """Suggest reducing number of threads"""
        suggested_threads = max(5, extra_threads // 2)
        
        self.log_action(
            "SUGGEST: Reduce Thread Count",
            f"Current: {extra_threads} threads → Suggested: {suggested_threads} threads"
        )
        
        print(f"{Colors.BOLD}Why this helps:{Colors.RESET}")
        print(f"  • Fewer threads = less competition for locks")
        print(f"  • Reduced context switching overhead")
        print(f"  • Lower memory usage\n")
        
        print(f"{Colors.BOLD}How to implement:{Colors.RESET}")
        print(f"  Modify contention_workload.py line 54:")
        print(f"  {Colors.YELLOW}workload.start(num_workers={suggested_threads}){Colors.RESET}")
        print(f"  (currently: num_workers=15)\n")
    
    def get_remediation_summary(self):
        """Get summary of all remediations performed"""
        if not self.remediation_log:
            return "No remediations performed yet"
        
        summary = f"\n{Colors.BOLD}REMEDIATION HISTORY{Colors.RESET}\n"
        summary += "─" * 80 + "\n"
        
        for entry in self.remediation_log[-5:]:  # Last 5
            summary += f"  {entry['timestamp'].strftime('%H:%M:%S')} - {entry['action']}\n"
            summary += f"    {entry['details']}\n"
        
        return summary
    
    def auto_restart_workload(self, current_intensity='high'):
        """
        Automatically restart workload with lower intensity.
        
        WARNING: This will kill Python processes!
        Only use if you're sure it's safe.
        """
        print(f"\n{Colors.RED}[AUTO-RESTART] Attempting to reduce workload intensity...{Colors.RESET}")
        
        # Find Python processes (excluding this monitor)
        import psutil
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if any('contention_workload' in str(arg) for arg in cmdline):
                        print(f"  Found workload process: PID {proc.info['pid']}")
                        print(f"  Terminating...")
                        
                        # Kill the process
                        proc.terminate()
                        proc.wait(timeout=5)
                        
                        print(f"  {Colors.GREEN}✓ Terminated{Colors.RESET}")
                        
                        # Restart with lower intensity
                        new_intensity = 'low' if current_intensity == 'high' else 'medium'
                        print(f"  Restarting with intensity: {new_intensity}")
                        
                        subprocess.Popen(
                            ['python', 'contention_workload.py', new_intensity],
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                        )
                        
                        self.log_action(
                            "AUTO-RESTART",
                            f"Killed PID {proc.info['pid']}, restarted with {new_intensity} intensity"
                        )
                        
                        return True
            except:
                pass
        
        print(f"  {Colors.YELLOW}No workload process found{Colors.RESET}")
        return False


# Example usage in monitor
def demo_remediation():
    """Demo of remediation system"""
    remediator = ContentionRemediator()
    
    # Simulate HIGH contention detection
    print(f"{Colors.CYAN}Simulating HIGH contention detection...{Colors.RESET}\n")
    
    metrics = {
        'avg_wait_time_ms': 120,
        'max_wait_time_ms': 350,
        'contention_frequency': 85,
        'blocked_thread_percentage': 45,
        'wait_time_growth_rate': 1.5
    }
    
    remediator.remediate_high_contention('HIGH', metrics, extra_threads=16)
    
    print(remediator.get_remediation_summary())

if __name__ == '__main__':
    demo_remediation()
