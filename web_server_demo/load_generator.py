"""
HTTP Load Generator
Generates HTTP traffic to create server thread contention
Automatically detects when servers are split
"""

import requests
import threading
import time
import sys

class LoadGenerator:
    """Generates HTTP load to create server contention"""
    
    def __init__(self, intensity='high'):
        self.running = False
        self.intensity = intensity
        self.servers = ['http://localhost:5000']  # Start with single server
        self.requests_sent = 0
        self.requests_failed = 0
        self.lock = threading.Lock()
        
        # Check if split servers exist
        self._check_for_split_servers()
    
    def _check_for_split_servers(self):
        """Check if servers on 5001/5002 are running (after split)"""
        try:
            # Try to connect to split servers
            r1 = requests.get('http://localhost:5001/stats', timeout=0.5)
            r2 = requests.get('http://localhost:5002/stats', timeout=0.5)
            
            # Both servers responding - use them!
            if r1.status_code == 200 and r2.status_code == 200:
                old_servers = self.servers.copy()
                self.servers = [
                    'http://localhost:5001',
                    'http://localhost:5002'
                ]
                # Only print if this is a new detection
                if old_servers != self.servers:
                    print(f"\n✓ Detected split servers - switching to ports 5001 & 5002\n")
                return True
        except:
            pass
        return False
    
    def send_requests(self, worker_id):
        """Worker thread that sends HTTP requests"""
        consecutive_failures = 0
        
        while self.running:
            try:
                # Check for split servers more frequently (every 10 requests)
                if self.requests_sent % 10 == 0:
                    self._check_for_split_servers()
                
                # Round-robin between servers
                server = self.servers[worker_id % len(self.servers)]
                
                # Send request
                response = requests.get(f"{server}/", timeout=2)
                
                if response.status_code == 200:
                    with self.lock:
                        self.requests_sent += 1
                    consecutive_failures = 0  # Reset on success
                
                # Intensity-based delay
                if self.intensity == 'low':
                    time.sleep(0.1)
                elif self.intensity == 'medium':
                    time.sleep(0.05)
                # high: minimal delay (creates more contention)
                
            except requests.exceptions.RequestException as e:
                with self.lock:
                    self.requests_failed += 1
                
                consecutive_failures += 1
                
                # If we have multiple failures, immediately check for split
                if consecutive_failures >= 3:
                    if self._check_for_split_servers():
                        consecutive_failures = 0  # Reset if we found new servers
                
                # Brief pause before retry
                time.sleep(0.2)
                
            except Exception:
                pass
    
    def start(self, num_workers=50):
        """Start load generation"""
        self.running = True
        
        print(f"\n{'='*60}")
        print(f"  HTTP Load Generator")
        print(f"{'='*60}")
        print(f"  Intensity: {self.intensity.upper()}")
        print(f"  Workers: {num_workers}")
        print(f"  Target servers: {', '.join(self.servers)}")
        print(f"{'='*60}\n")
        
        workers = []
        for i in range(num_workers):
            t = threading.Thread(
                target=self.send_requests,
                args=(i,),
                daemon=True
            )
            t.start()
            workers.append(t)
        
        try:
            while True:
                time.sleep(5)
                print(f"Requests: {self.requests_sent:6d} success, {self.requests_failed:4d} failed | Servers: {len(self.servers)}")
        except KeyboardInterrupt:
            print("\n\n✓ Stopping load generator...")
            self.running = False
            time.sleep(1)
            print(f"Final stats: {self.requests_sent} requests sent to {len(self.servers)} server(s)")
            print("✓ Done!")

def main():
    intensity = 'high'
    if len(sys.argv) > 1:
        intensity = sys.argv[1].lower()
        if intensity not in ['low', 'medium', 'high']:
            print("Usage: python load_generator.py [low|medium|high]")
        else :
            if intensity == 'low':
                num_workers=30
            elif intensity == 'medium':
                num_workers = 70
            elif intensity == 'high':
                num_workers = 80
            generator = LoadGenerator(intensity=intensity)
            generator.start(num_workers)

if __name__ == '__main__':
    main()
