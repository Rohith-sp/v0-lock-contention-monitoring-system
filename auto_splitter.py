"""
Automatic Process Splitting for Contention Reduction
Actually kills and restarts processes with lower thread counts
"""

import psutil
import subprocess
import os
import time
import sys

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'

class AutoSplitter:
    """
    Automatically splits high-contention Python processes.
    
    When HIGH contention detected:
    1. Find the contention_workload.py process
    2. Ask user permission
    3. Kill the process
    4. Start 2 new processes with half the threads each
    """
    
    def __init__(self):
        self.split_count = 0
        self.last_split_time = None
        self.cooldown_seconds = 10  # Reduced for demo (was 60)
    
    def can_split(self):
        """Check if enough time passed since last split"""
        if self.last_split_time is None:
            return True
        
        elapsed = time.time() - self.last_split_time
        return elapsed > self.cooldown_seconds
    
    def find_workload_process(self):
        """Find contention_workload.py or web_server.py process"""
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'num_threads']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    cmdline_str = ' '.join(str(arg) for arg in cmdline)
                    
                    # Check for contention_workload
                    if 'contention_workload' in cmdline_str:
                        intensity = 'high'  # default
                        for arg in cmdline:
                            if arg in ['low', 'medium', 'high']:
                                intensity = arg
                        
                        return {
                            'pid': proc.info['pid'],
                            'threads': proc.info['num_threads'],
                            'intensity': intensity,
                            'script': 'contention_workload',
                            'process': proc
                        }
                    
                    # Check for web_server
                    elif 'web_server' in cmdline_str:
                        port = '5000'  # default
                        for arg in cmdline:
                            if arg.isdigit() and int(arg) >= 5000:
                                port = arg
                        
                        return {
                            'pid': proc.info['pid'],
                            'threads': proc.info['num_threads'],
                            'port': port,
                            'script': 'web_server',
                            'process': proc
                        }
                        
            except:
                pass
        
        return None
    
    def ask_permission(self, workload_info):
        """Ask user if they want to split the process"""
        script_type = workload_info.get('script', 'contention_workload')
        
        print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}  [!] HIGH CONTENTION DETECTED{Colors.RESET}")
        print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}Detected Process:{Colors.RESET}")
        print(f"  PID: {workload_info['pid']}")
        print(f"  Threads: {workload_info['threads']}")
        
        if script_type == 'web_server':
            print(f"  Port: {workload_info.get('port', '5000')}\n")
            
            print(f"{Colors.BOLD}Proposed Solution:{Colors.RESET}")
            print(f"  Kill current server (port {workload_info.get('port', '5000')})")
            print(f"  Start 2 new servers (ports 5001 & 5002)")
            print(f"  Reduce load per instance by 50%\n")
        else:
            intensity = workload_info.get('intensity', 'high')
            print(f"  Intensity: {intensity.upper()}\n")
            
            print(f"{Colors.BOLD}Proposed Solution:{Colors.RESET}")
            print(f"  Kill current process (PID {workload_info['pid']})")
            print(f"  Start 2 new processes with {workload_info['threads']//2} threads each")
            print(f"  Reduce intensity: {intensity} → low\n")
        
        print(f"{Colors.YELLOW}Do you want to proceed? (y/n): {Colors.RESET}", end='')
        
        # Non-blocking input with timeout
        try:
            import msvcrt
            import time
            
            print(f"\n{Colors.GRAY}(Auto-declining in 10 seconds if no input...){Colors.RESET}")
            
            start_time = time.time()
            response = ''
            
            while time.time() - start_time < 10:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode('utf-8').lower()
                    response = char
                    break
                time.sleep(0.1)
            
            print(f"\nResponse: {response if response else 'timeout'}\n")
            return response == 'y'
        
        except:
            # Fallback for non-Windows
            response = input().lower()
            return response == 'y'
    
    def split_process(self, workload_info):
        """Actually split the process"""
        if not self.can_split():
            remaining = self.cooldown_seconds - (time.time() - self.last_split_time)
            print(f"{Colors.YELLOW}  Cooldown active ({remaining:.0f}s remaining){Colors.RESET}\n")
            return False
        
        print(f"{Colors.CYAN}[SPLITTING] Starting process split...{Colors.RESET}\n")
        
        # Step 1: Kill the current process
        print(f"  1. Terminating PID {workload_info['pid']}...")
        try:
            workload_info['process'].terminate()
            workload_info['process'].wait(timeout=5)
            print(f"     {Colors.GREEN}✓ Process terminated{Colors.RESET}\n")
        except Exception as e:
            print(f"     {Colors.RED}✗ Failed to terminate: {e}{Colors.RESET}\n")
            return False
        
        # Step 2: Start 2 new processes
        print(f"  2. Starting 2 new processes...")
        
        # Get the script path
        script_root = os.path.dirname(os.path.abspath(__file__))
        script_name = workload_info.get('script', 'contention_workload')
        
        # Try root first, then web_server_demo folder
        script_path = os.path.join(script_root, f'{script_name}.py')
        if not os.path.exists(script_path):
            script_path = os.path.join(script_root, 'web_server_demo', f'{script_name}.py')
            
        script_dir = os.path.dirname(script_path)
        
        print(f"     Script: {script_name}.py")
        print(f"     Working Directory: {script_dir}")
        print(f"     Full Path: {script_path}")
        
        if not os.path.exists(script_path):
            print(f"     {Colors.RED}✗ Script not found: {script_path}{Colors.RESET}\n")
            print(f"     Looking for files in {script_dir}:")
            try:
                files = [f for f in os.listdir(script_dir) if f.endswith('.py')]
                for f in files[:5]:
                    print(f"       - {f}")
            except:
                pass
            return False
        
        try:
            # Different handling for web servers vs workloads
            if script_name == 'web_server':
                # Web server: start on ports 5001 and 5002
                print(f"     Starting web server 1 on port 5001...")
                cmd1 = f'start "Web-Server-1" /D "{script_dir}" cmd /K {sys.executable} {script_path} 5001'
                subprocess.Popen(cmd1, shell=True)
                print(f"     {Colors.GREEN}✓ Server 1 started (port 5001){Colors.RESET}")
                
                time.sleep(2)
                
                print(f"     Starting web server 2 on port 5002...")
                cmd2 = f'start "Web-Server-2" /D "{script_dir}" cmd /K {sys.executable} {script_path} 5002'
                subprocess.Popen(cmd2, shell=True)
                print(f"     {Colors.GREEN}✓ Server 2 started (port 5002){Colors.RESET}\n")
                
            else:
                # Regular workload: start with 'low' intensity
                print(f"     Starting process 1...")
                cmd1 = f'start "Workload-1" /D "{script_dir}" cmd /K {sys.executable} {script_path} low'
                print(f"     Command: {cmd1}")
                subprocess.Popen(cmd1, shell=True)
                print(f"     {Colors.GREEN}✓ Process 1 window opened{Colors.RESET}")
                
                time.sleep(2)
                
                print(f"     Starting process 2...")
                cmd2 = f'start "Workload-2" /D "{script_dir}" cmd /K {sys.executable} {script_path} low'
                print(f"     Command: {cmd2}")
                subprocess.Popen(cmd2, shell=True)
                print(f"     {Colors.GREEN}✓ Process 2 window opened{Colors.RESET}\n")
            
            
            print(f"{Colors.GREEN}{'='*80}{Colors.RESET}")
            print(f"{Colors.GREEN}{Colors.BOLD}  ✓ SPLIT COMPLETE{Colors.RESET}")
            print(f"{Colors.GREEN}{'='*80}{Colors.RESET}\n")
            
            print(f"{Colors.BOLD}Result:{Colors.RESET}")
            if script_name == 'web_server':
                print(f"  Before: 1 server on port {workload_info.get('port', '5000')} × {workload_info['threads']} threads")
                print(f"  After:  2 servers (ports 5001 & 5002) × ~{workload_info['threads']//2} threads each")
                print(f"\n  {Colors.CYAN}You should see 2 new windows: 'Web-Server-1' and 'Web-Server-2'{Colors.RESET}\n")
            else:
                print(f"  Before: 1 process × {workload_info['threads']} threads (HIGH intensity)")
                print(f"  After:  2 processes (LOW intensity)")
                print(f"\n  {Colors.CYAN}You should see 2 new windows: 'Workload-1' and 'Workload-2'{Colors.RESET}\n")
            
            self.split_count += 1
            self.last_split_time = time.time()
            
            return True
        
        except Exception as e:
            print(f"     {Colors.RED}✗ Failed to start new processes: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
            return False
    
    def auto_remediate(self, risk_level):
        """Main entry point - called when HIGH contention detected"""
        if risk_level != 'HIGH':
            return False
        
        # Find the workload process
        workload = self.find_workload_process()
        
        if not workload:
            print(f"{Colors.YELLOW}⚠ No workload process found to split{Colors.RESET}\n")
            return False
        
        # Ask permission
        if not self.ask_permission(workload):
            print(f"{Colors.YELLOW}✗ Split cancelled by user{Colors.RESET}\n")
            return False
        
        # Do the split
        return self.split_process(workload)
    
    def get_stats(self):
        """Get remediation statistics"""
        return {
            'total_splits': self.split_count,
            'last_split': self.last_split_time
        }


# Demo
if __name__ == '__main__':
    print(f"{Colors.CYAN}Auto-Splitter Demo{Colors.RESET}\n")
    
    splitter = AutoSplitter()
    
    # Find workload
    workload = splitter.find_workload_process()
    
    if workload:
        print(f"Found workload: PID {workload['pid']}, {workload['threads']} threads\n")
        
        # Simulate HIGH contention
        if splitter.ask_permission(workload):
            splitter.split_process(workload)
    else:
        print("No workload process running")
        print("Start with: python contention_workload.py high")
