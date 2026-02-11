"""
Simple Lock Contention Workload Generator
Creates REAL thread contention that the monitor can detect
"""

import threading
import time
import random

class ContentionWorkload:
    """Creates actual lock contention with real threads"""
    
    def __init__(self, intensity='low'):
        self.intensity = intensity
        self.running = False
        self.locks = {
            'database_lock': threading.Lock(),
            'cache_lock': threading.Lock(),
            'file_lock': threading.Lock(),
        }
        self.lock_stats = {name: 0 for name in self.locks.keys()}
        
    def worker(self, worker_id):
        """Worker thread that creates lock contention"""
        while self.running:
            # Pick a random lock
            lock_name = random.choice(list(self.locks.keys()))
            lock = self.locks[lock_name]
            
            # Try to acquire lock
            lock.acquire()
            try:
                self.lock_stats[lock_name] += 1
                
                # Hold lock for varying durations based on intensity
                if self.intensity == 'low':
                    time.sleep(random.uniform(0.001, 0.005))  # 1-5ms
                elif self.intensity == 'medium':
                    time.sleep(random.uniform(0.01, 0.05))    # 10-50ms
                else:  # high
                    time.sleep(random.uniform(0.05, 0.2))     # 50-200ms
            finally:
                lock.release()
            
            # Sleep between operations
            if self.intensity == 'low':
                time.sleep(random.uniform(0.05, 0.1))
            elif self.intensity == 'medium':
                time.sleep(random.uniform(0.01, 0.05))
            else:  # high
                time.sleep(random.uniform(0.001, 0.01))
    
    def start(self, num_workers=30):
        """Start workload"""
        self.running = True
        
        print(f"\n  Starting contention workload")
        print(f"   Intensity: {self.intensity.upper()}")
        print(f"   Workers: {num_workers}")
        print(f"   This creates REAL thread contention!\n")
        
        workers = []
        for i in range(num_workers):
            t = threading.Thread(
                target=self.worker, 
                args=(i,),
                name=f"Worker-{i}",
                daemon=True
            )
            t.start()
            workers.append(t)
        
        try:
            while True:
                time.sleep(5)
                print(f"Lock acquisitions: {self.lock_stats}")
        except KeyboardInterrupt:
            print("\n\n✓ Stopping workload...")
            self.running = False
            time.sleep(1)
            print(f"Final stats: {self.lock_stats}")
            print("✓ Done!")

def main():
    import sys
    
    intensity = 'medium'
    if len(sys.argv) > 1:
        intensity = sys.argv[1].lower()
        if intensity not in ['low', 'medium', 'high']:
            print("Usage: python contention_workload.py [low|medium|high]")
            intensity = 'medium'
        if intensity == 'high':
            num_workers = 90
        elif intensity == 'medium':
            num_workers = 55
        else:
            num_workers = 1
    workload = ContentionWorkload(intensity=intensity)
    workload.start(num_workers=num_workers)

if __name__ == '__main__':
    main()
