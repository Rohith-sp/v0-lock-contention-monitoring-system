"""
Lock Contention Monitoring Dashboard (CLI)

Real-time terminal interface displaying:
- Live contention metrics (simulated)
- Top contended locks
- Blocked thread percentage
- Predicted contention risk

Usage:
    python scripts/cli_monitor.py [--interval SECONDS]
"""

import time
import argparse
import os
import sys
from datetime import datetime
from predict import ContentionPredictor
import numpy as np

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'

class LockMonitor:
    """Simulates lock contention monitoring with realistic metrics."""
    
    def __init__(self):
        self.predictor = None
        self.iteration = 0
        self.prev_avg_wait = 10.0
        
        # Simulated lock names
        self.lock_names = [
            'db_connection_pool',
            'user_session_cache',
            'order_processing_queue',
            'inventory_update_lock',
            'payment_gateway_sync',
            'logging_buffer',
            'metrics_aggregator',
            'auth_token_cache'
        ]
    
    def load_predictor(self):
        """Load ML model for predictions."""
        try:
            self.predictor = ContentionPredictor()
            return True
        except FileNotFoundError:
            print(f"{Colors.YELLOW}Warning: Model not found. Run training first.{Colors.RESET}")
            print(f"{Colors.YELLOW}Continuing without predictions...{Colors.RESET}\n")
            return False
    
    def generate_live_metrics(self):
        """
        Simulate realistic lock contention metrics with temporal dynamics.
        Metrics evolve over time to create realistic monitoring experience.
        """
        
        self.iteration += 1
        
        # Simulate gradual increase in contention over time
        # Then occasional drops (like after deployments or off-peak hours)
        if self.iteration % 20 == 0:
            # Simulate contention relief
            base_multiplier = np.random.uniform(0.3, 0.6)
        elif self.iteration % 5 == 0:
            # Periodic spike
            base_multiplier = np.random.uniform(1.2, 2.0)
        else:
            # Gradual drift
            base_multiplier = np.random.uniform(0.9, 1.1)
        
        # Generate correlated metrics
        avg_wait = max(5.0, self.prev_avg_wait * base_multiplier + np.random.normal(0, 5))
        max_wait = avg_wait * np.random.uniform(2.0, 5.0)
        
        # Frequency correlates with wait time
        frequency = int(max(1, 10 + (avg_wait / 5) + np.random.poisson(5)))
        
        # Blocked percentage increases with wait time
        blocked_pct = min(95.0, max(1.0, (avg_wait / 10) * 5 + np.random.uniform(0, 10)))
        
        # Growth rate based on recent trend
        growth_rate = (avg_wait - self.prev_avg_wait) / max(self.prev_avg_wait, 1.0)
        
        self.prev_avg_wait = avg_wait
        
        metrics = {
            'avg_wait_time_ms': round(avg_wait, 2),
            'max_wait_time_ms': round(max_wait, 2),
            'contention_frequency': frequency,
            'blocked_thread_percentage': round(blocked_pct, 2),
            'wait_time_growth_rate': round(growth_rate, 2)
        }
        
        return metrics
    
    def generate_lock_table(self, metrics):
        """Generate simulated top contended locks."""
        
        # Select 5 random locks and assign contention stats
        selected_locks = np.random.choice(self.lock_names, size=5, replace=False)
        
        lock_stats = []
        total_contentions = metrics['contention_frequency']
        
        # Distribute contentions with realistic skew (few locks dominate)
        weights = np.random.pareto(2, size=5) + 1
        weights = weights / weights.sum()
        
        for lock_name, weight in zip(selected_locks, weights):
            contentions = int(total_contentions * weight)
            wait_time = metrics['avg_wait_time_ms'] * np.random.uniform(0.5, 1.5)
            
            lock_stats.append({
                'name': lock_name,
                'contentions': contentions,
                'avg_wait_ms': round(wait_time, 1)
            })
        
        # Sort by contentions descending
        lock_stats.sort(key=lambda x: x['contentions'], reverse=True)
        
        return lock_stats
    
    def display_dashboard(self, metrics, lock_stats, prediction=None):
        """Render dashboard to terminal."""
        
        # Clear screen (works on Unix/Linux/Mac)
        os.system('clear' if os.name != 'nt' else 'cls')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Header
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  LOCK CONTENTION MONITOR{Colors.RESET}")
        print(f"{Colors.GRAY}  {timestamp}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        # Live Metrics
        print(f"{Colors.BOLD}LIVE METRICS{Colors.RESET}")
        print(f"{Colors.GRAY}{'─'*70}{Colors.RESET}")
        
        # Color code based on severity
        wait_color = self._get_metric_color(metrics['avg_wait_time_ms'], 50, 150)
        freq_color = self._get_metric_color(metrics['contention_frequency'], 15, 40)
        blocked_color = self._get_metric_color(metrics['blocked_thread_percentage'], 15, 40)
        
        print(f"  Avg Wait Time:        {wait_color}{metrics['avg_wait_time_ms']:>8.2f} ms{Colors.RESET}")
        print(f"  Max Wait Time:        {Colors.RESET}{metrics['max_wait_time_ms']:>8.2f} ms")
        print(f"  Contention Events:    {freq_color}{metrics['contention_frequency']:>8}{Colors.RESET}")
        print(f"  Blocked Threads:      {blocked_color}{metrics['blocked_thread_percentage']:>7.1f} %{Colors.RESET}")
        print(f"  Wait Time Growth:     {Colors.RESET}{metrics['wait_time_growth_rate']:>8.2f}")
        print()
        
        # Top Contended Locks
        print(f"{Colors.BOLD}TOP CONTENDED LOCKS{Colors.RESET}")
        print(f"{Colors.GRAY}{'─'*70}{Colors.RESET}")
        print(f"  {'Lock Name':<30} {'Contentions':>12} {'Avg Wait':>12}")
        print(f"{Colors.GRAY}  {'-'*30} {'-'*12} {'-'*12}{Colors.RESET}")
        
        for lock in lock_stats:
            print(f"  {lock['name']:<30} {lock['contentions']:>12} {lock['avg_wait_ms']:>10.1f} ms")
        print()
        
        # ML Prediction
        if prediction:
            risk_level, probabilities = prediction
            risk_color = self._get_risk_color(risk_level)
            
            print(f"{Colors.BOLD}PREDICTED CONTENTION RISK{Colors.RESET}")
            print(f"{Colors.GRAY}{'─'*70}{Colors.RESET}")
            print(f"  Risk Level: {risk_color}{Colors.BOLD}{risk_level}{Colors.RESET}")
            print(f"  Confidence: LOW={probabilities['LOW']:.1%}  "
                  f"MEDIUM={probabilities['MEDIUM']:.1%}  "
                  f"HIGH={probabilities['HIGH']:.1%}")
            print()
        
        # Footer
        print(f"{Colors.GRAY}{'─'*70}{Colors.RESET}")
        print(f"{Colors.GRAY}  Press Ctrl+C to stop monitoring{Colors.RESET}")
    
    def _get_metric_color(self, value, warn_threshold, critical_threshold):
        """Return color based on metric thresholds."""
        if value >= critical_threshold:
            return Colors.RED
        elif value >= warn_threshold:
            return Colors.YELLOW
        return Colors.GREEN
    
    def _get_risk_color(self, risk_level):
        """Return color for risk level."""
        if risk_level == 'HIGH':
            return Colors.RED
        elif risk_level == 'MEDIUM':
            return Colors.YELLOW
        return Colors.GREEN
    
    def run(self, interval=2):
        """
        Run monitoring loop.
        
        Args:
            interval: Update interval in seconds
        """
        
        has_predictor = self.load_predictor()
        
        print(f"{Colors.CYAN}Starting lock contention monitor...{Colors.RESET}")
        print(f"{Colors.GRAY}Update interval: {interval}s{Colors.RESET}\n")
        time.sleep(2)
        
        try:
            while True:
                # Generate live metrics
                metrics = self.generate_live_metrics()
                
                # Generate lock contention table
                lock_stats = self.generate_lock_table(metrics)
                
                # Get prediction if model available
                prediction = None
                if has_predictor:
                    risk_level, probs = self.predictor.predict(metrics)
                    prediction = (risk_level, probs)
                
                # Display dashboard
                self.display_dashboard(metrics, lock_stats, prediction)
                
                # Wait for next update
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Monitoring stopped.{Colors.RESET}")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description='Lock Contention Monitoring Dashboard'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=2.0,
        help='Update interval in seconds (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    monitor = LockMonitor()
    monitor.run(interval=args.interval)

if __name__ == '__main__':
    main()
