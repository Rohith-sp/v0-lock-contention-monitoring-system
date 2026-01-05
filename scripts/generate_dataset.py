"""
Lock Contention Dataset Generator

Generates realistic dummy lock contention metrics for ML training.
Each row represents aggregated metrics over a fixed time window (e.g., 10 seconds).

Features:
- avg_wait_time_ms: Average time threads wait for locks
- max_wait_time_ms: Maximum wait time in the window
- contention_frequency: Number of contention events
- blocked_thread_percentage: % of threads blocked
- wait_time_growth_rate: Rate of increase in wait times

Labels:
- LOW: Normal operation, minimal contention
- MEDIUM: Elevated contention, monitor closely
- HIGH: Critical contention, immediate attention needed
"""

import numpy as np
import pandas as pd
from typing import Literal

# Seed for reproducibility
np.random.seed(42)

# Dataset size
NUM_SAMPLES = 1000

def generate_contention_metrics():
    """
    Generate realistic lock contention metrics using statistical distributions.
    
    Simulates three operational states:
    - Normal: 60% of samples - low contention
    - Elevated: 30% of samples - medium contention
    - Critical: 10% of samples - high contention
    """
    
    # Determine operational state for each sample
    states = np.random.choice(['normal', 'elevated', 'critical'], 
                             size=NUM_SAMPLES, 
                             p=[0.6, 0.3, 0.1])
    
    data = []
    
    for state in states:
        if state == 'normal':
            # Normal operation: low contention
            avg_wait = np.random.gamma(2, 5)  # Mean ~10ms
            max_wait = avg_wait * np.random.uniform(1.5, 3.0)
            frequency = np.random.poisson(5)  # Low frequency
            blocked_pct = np.random.beta(2, 10) * 20  # Usually < 5%
            growth_rate = np.random.normal(0.0, 0.5)  # Stable
            
        elif state == 'elevated':
            # Elevated contention: starting to see issues
            avg_wait = np.random.gamma(5, 10)  # Mean ~50ms
            max_wait = avg_wait * np.random.uniform(2.0, 4.0)
            frequency = np.random.poisson(20)  # Moderate frequency
            blocked_pct = np.random.beta(4, 6) * 40  # 10-30%
            growth_rate = np.random.normal(1.0, 0.8)  # Increasing
            
        else:  # critical
            # Critical contention: system under stress
            avg_wait = np.random.gamma(10, 20)  # Mean ~200ms
            max_wait = avg_wait * np.random.uniform(3.0, 6.0)
            frequency = np.random.poisson(50)  # High frequency
            blocked_pct = np.random.beta(8, 2) * 60 + 30  # 30-90%
            growth_rate = np.random.normal(3.0, 1.5)  # Rapidly increasing
        
        data.append({
            'avg_wait_time_ms': round(avg_wait, 2),
            'max_wait_time_ms': round(max_wait, 2),
            'contention_frequency': int(frequency),
            'blocked_thread_percentage': round(blocked_pct, 2),
            'wait_time_growth_rate': round(growth_rate, 2)
        })
    
    return pd.DataFrame(data)

def label_contention_risk(row) -> Literal['LOW', 'MEDIUM', 'HIGH']:
    """
    Rule-based labeling logic for contention risk.
    
    Labeling criteria:
    - HIGH: Any critical metric threshold exceeded
    - MEDIUM: Multiple elevated metrics
    - LOW: All metrics in normal range
    """
    
    # Critical thresholds (any triggers HIGH)
    if (row['avg_wait_time_ms'] > 150 or 
        row['max_wait_time_ms'] > 500 or
        row['blocked_thread_percentage'] > 40 or
        row['contention_frequency'] > 40):
        return 'HIGH'
    
    # Elevated thresholds (multiple triggers MEDIUM)
    warning_count = 0
    if row['avg_wait_time_ms'] > 50:
        warning_count += 1
    if row['max_wait_time_ms'] > 200:
        warning_count += 1
    if row['blocked_thread_percentage'] > 15:
        warning_count += 1
    if row['contention_frequency'] > 15:
        warning_count += 1
    if row['wait_time_growth_rate'] > 1.0:
        warning_count += 1
    
    if warning_count >= 2:
        return 'MEDIUM'
    
    return 'LOW'

def generate_dataset(output_path: str = 'lock_contention_dataset.csv'):
    """
    Generate complete dataset with features and labels.
    """
    print(f"Generating {NUM_SAMPLES} samples of lock contention data...")
    
    # Generate features
    df = generate_contention_metrics()
    
    # Apply labeling logic
    df['contention_risk_label'] = df.apply(label_contention_risk, axis=1)
    
    # Display statistics
    print("\n=== Dataset Statistics ===")
    print(f"Total samples: {len(df)}")
    print(f"\nLabel distribution:")
    print(df['contention_risk_label'].value_counts())
    print(f"\nFeature statistics:")
    print(df.describe())
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\n✓ Dataset saved to {output_path}")
    
    return df

if __name__ == '__main__':
    dataset = generate_dataset()
