"""
Windows Lock Contention Inference via psutil
IMPORTANT: This is INFERENCE, not direct measurement
"""

import psutil
import time
from collections import deque
from datetime import datetime
from typing import Dict, Optional

class WindowsContentionInferrer:
    """
    Infers lock contention from Windows process/thread metrics.
    
    LIMITATIONS (MUST ACKNOWLEDGE):
    - Cannot directly observe pthread mutex locks
    - Cannot measure actual lock wait times
    - Relies on indirect indicators (thread states, I/O wait, context switches)
    - Lower precision than Linux eBPF
    - Results are HEURISTIC, not measured
    """
    
    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = sample_interval
        self.history = deque(maxlen=100)  # Keep last 100 samples
        self.baseline_ctx_switches = None
    
    def infer_system_contention(self) -> Dict:
        """
        Infer system-wide contention from observable Windows metrics.
        
        Returns dict with INFERRED metrics (not measured):
        {
            'num_threads': total threads across monitored processes,
            'threads_waiting': inferred count (from I/O wait),
            'io_wait_time': percentage (indirect indicator),
            'ctx_switches': context switch rate (contention proxy),
            'has_thread_states': bool (data quality indicator)
        }
        """
        total_threads = 0
        threads_waiting = 0  # Inferred from I/O wait
        total_io_wait = 0.0
        ctx_switches = 0
        process_count = 0
        
        # Sample system-wide CPU stats
        cpu_times_start = psutil.cpu_times()
        time.sleep(self.sample_interval)
        cpu_times_end = psutil.cpu_times()
        
        # Calculate I/O wait percentage (indirect contention indicator)
        if hasattr(cpu_times_end, 'iowait') and hasattr(cpu_times_start, 'iowait'):
            io_wait_delta = cpu_times_end.iowait - cpu_times_start.iowait
            total_time = sum(cpu_times_end) - sum(cpu_times_start)
            io_wait_pct = (io_wait_delta / total_time * 100) if total_time > 0 else 0
        else:
            # Windows doesn't have iowait - use idle as inverse proxy
            idle_delta = cpu_times_end.idle - cpu_times_start.idle
            total_time = sum(cpu_times_end) - sum(cpu_times_start)
            io_wait_pct = max(0, 100 - (idle_delta / total_time * 100)) if total_time > 0 else 0
        
        # Get context switch rate (proxy for contention)
        ctx_switch_stats = psutil.cpu_stats()
        if self.baseline_ctx_switches is None:
            self.baseline_ctx_switches = ctx_switch_stats.ctx_switches
        ctx_switches = ctx_switch_stats.ctx_switches - self.baseline_ctx_switches
        self.baseline_ctx_switches = ctx_switch_stats.ctx_switches
        
        # Sample multi-threaded processes (potential lock users)
        for proc in psutil.process_iter(['pid', 'name', 'num_threads']):
            try:
                info = proc.info
                if info['num_threads'] > 1:  # Only multi-threaded processes
                    total_threads += info['num_threads']
                    process_count += 1
                    
                    # Try to get thread-level info (not always available)
                    try:
                        proc_obj = psutil.Process(info['pid'])
                        threads = proc_obj.threads()
                        
                        # Infer waiting threads from system time vs user time ratio
                        # High system time suggests kernel operations (locks, I/O)
                        cpu_times = proc_obj.cpu_times()
                        if cpu_times.system > cpu_times.user * 0.5:
                            # Heuristic: if system time > 50% of user time, 
                            # assume some threads are blocked
                            threads_waiting += max(1, info['num_threads'] // 4)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
        
        # Normalize context switches per second
        ctx_switches_per_sec = ctx_switches / self.sample_interval if self.sample_interval > 0 else 0
        
        metrics = {
            'num_threads': total_threads,
            'threads_waiting': threads_waiting,  # INFERRED, not measured
            'io_wait_time': io_wait_pct,  # Indirect indicator
            'ctx_switches': int(ctx_switches_per_sec),  # Proxy metric
            'has_thread_states': process_count > 0,  # Data quality flag
            'open_handles': self._estimate_handle_contention(),
        }
        
        # Store in history
        self.history.append({
            'timestamp': datetime.now(),
            'metrics': metrics
        })
        
        return metrics
    
    def _estimate_handle_contention(self) -> int:
        """
        Estimate file handle contention (another indirect indicator).
        High handle count suggests potential file lock contention.
        """
        total_handles = 0
        for proc in psutil.process_iter(['pid']):
            try:
                proc_obj = psutil.Process(proc.info['pid'])
                # num_handles() is Windows-specific
                if hasattr(proc_obj, 'num_handles'):
                    total_handles += proc_obj.num_handles()
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        return total_handles
    
    def get_contention_trend(self) -> float:
        """
        Calculate contention trend from historical data.
        Returns growth rate (-2 to +5 range).
        """
        if len(self.history) < 20:
            return 0.0
        
        # Compare recent vs older samples
        recent = [h['metrics']['threads_waiting'] for h in list(self.history)[-10:]]
        older = [h['metrics']['threads_waiting'] for h in list(self.history)[-20:-10]]
        
        recent_avg = sum(recent) / len(recent) if recent else 0
        older_avg = sum(older) / len(older) if older else 0
        
        if older_avg == 0:
            return 0.0
        
        growth_rate = (recent_avg - older_avg) / older_avg
        return max(-2, min(5, growth_rate))
    
    def get_inference_quality(self) -> str:
        """
        Report data quality level.
        
        Returns: 'LOW', 'MEDIUM', or 'HIGH'
        """
        if len(self.history) < 10:
            return 'LOW'  # Insufficient history
        
        latest = self.history[-1]['metrics']
        
        if latest['has_thread_states'] and latest['num_threads'] > 10:
            return 'MEDIUM'  # Have thread data and sufficient processes
        else:
            return 'LOW'  # Limited observability
    
    
    def get_top_processes(self, limit=5):
        """
        Get top multi-threaded processes with thread details.
        
        Returns list of dicts with process info and thread IDs.
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'num_threads']):
            try:
                info = proc.info
                if info['num_threads'] > 1:  # Only multi-threaded
                    proc_obj = psutil.Process(info['pid'])
                    
                    # Get thread IDs
                    try:
                        threads = proc_obj.threads()
                        thread_ids = [t.id for t in threads[:5]]  # First 5 threads
                    except:
                        thread_ids = []
                    
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'num_threads': info['num_threads'],
                        'thread_ids': thread_ids
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by thread count
        processes.sort(key=lambda x: x['num_threads'], reverse=True)
        return processes[:limit]
    
    def get_limitations_disclaimer(self) -> str:
        """Return honest disclaimer about inference limitations"""
        return """
        WINDOWS INFERENCE LIMITATIONS:
        - Cannot directly measure lock wait times
        - Thread waiting count is INFERRED from system/user time ratio
        - I/O wait is used as indirect contention indicator
        - Context switches are a PROXY for lock contention
        - Confidence is LOWER than Linux eBPF measurements
        - Results are HEURISTIC, not precise measurements
        """

