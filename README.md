# Lock Contention Monitoring & Prediction System

A complete CLI-driven system for monitoring lock contention metrics and predicting contention risk using machine learning.

## Project Overview

This system demonstrates a practical approach to runtime lock contention monitoring with ML-based risk prediction. It consists of three integrated layers:

1. **Backend Monitoring Layer**: Simulates realistic lock contention data
2. **ML Analysis Layer**: Trains a model to predict contention risk (LOW/MEDIUM/HIGH)
3. **CLI Interface**: Real-time terminal dashboard displaying metrics and predictions

### Key Features

- Auto-generated dummy dataset (no external data required)
- Lightweight ML model (Logistic Regression) for interpretability
- Live terminal dashboard with color-coded metrics
- Predicts lock contention risk only (no CPU, latency, or deadlock prediction)
- Clean, minimal, and defensible implementation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Monitor Dashboard                     │
│  (Live metrics, top locks, predicted risk, visual display)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ML Prediction Engine                       │
│        (Logistic Regression, risk classification)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Backend Monitoring Simulator                   │
│         (Generate realistic contention metrics)             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

```bash
pip install numpy pandas scikit-learn
```

### Run Complete System

The easiest way to run everything:

```bash
python scripts/run_complete_system.py
```

This will:
1. Generate 1000 samples of lock contention data
2. Train the ML model
3. Launch the live monitoring dashboard

### Run Individual Components

**1. Generate Dataset**
```bash
python scripts/generate_dataset.py
```

Outputs: `lock_contention_dataset.csv`

**2. Train Model**
```bash
python scripts/train_model.py
```

Outputs: `model.pkl`, `scaler.pkl`, `model_metadata.pkl`

**3. Launch Monitor**
```bash
python scripts/cli_monitor.py --interval 2
```

Press Ctrl+C to stop monitoring.

## Dataset Schema

The system generates the following features for each time window:

| Feature | Description | Unit |
|---------|-------------|------|
| `avg_wait_time_ms` | Average time threads wait for locks | milliseconds |
| `max_wait_time_ms` | Maximum wait time in window | milliseconds |
| `contention_frequency` | Number of contention events | count |
| `blocked_thread_percentage` | Percentage of threads blocked | % |
| `wait_time_growth_rate` | Rate of increase in wait times | ratio |
| `contention_risk_label` | Risk level (LOW/MEDIUM/HIGH) | category |

### Dataset Generation Strategy

Data is generated using statistical distributions to simulate three operational states:

- **Normal (60%)**: Low contention, typical operation
  - Avg wait: ~10ms, Blocked threads: <5%
  
- **Elevated (30%)**: Increased contention, monitoring needed
  - Avg wait: ~50ms, Blocked threads: 10-30%
  
- **Critical (10%)**: High contention, immediate attention required
  - Avg wait: ~200ms, Blocked threads: 30-90%

## ML Model Details

### Model Choice: Logistic Regression

**Rationale:**
- Fast training and prediction (suitable for real-time systems)
- Interpretable coefficients (can explain which features drive risk)
- Sufficient accuracy for 3-class problem
- No complex hyperparameter tuning needed
- Lightweight deployment footprint

**Alternatives considered:**
- Random Forest: More accurate but less interpretable
- Neural Networks: Overkill for this problem size
- Decision Trees: Too prone to overfitting

### Labeling Logic

Risk levels are assigned using rule-based thresholds:

**HIGH Risk** (any condition triggers):
- avg_wait_time_ms > 150
- max_wait_time_ms > 500
- blocked_thread_percentage > 40
- contention_frequency > 40

**MEDIUM Risk** (2+ conditions trigger):
- avg_wait_time_ms > 50
- max_wait_time_ms > 200
- blocked_thread_percentage > 15
- contention_frequency > 15
- wait_time_growth_rate > 1.0

**LOW Risk**:
- All metrics in normal range

### Feature Engineering

All features are standardized (mean=0, std=1) before training to ensure:
- Equal feature importance initially
- Faster convergence
- Better numerical stability

## Example Terminal Output

```
======================================================================
  LOCK CONTENTION MONITOR
  2025-01-05 14:32:15
======================================================================

LIVE METRICS
──────────────────────────────────────────────────────────────────────
  Avg Wait Time:            45.23 ms
  Max Wait Time:           189.45 ms
  Contention Events:           18
  Blocked Threads:           12.5 %
  Wait Time Growth:           0.85

TOP CONTENDED LOCKS
──────────────────────────────────────────────────────────────────────
  Lock Name                      Contentions      Avg Wait
  ------------------------------ ------------ ------------
  db_connection_pool                        7       52.3 ms
  user_session_cache                        4       38.7 ms
  order_processing_queue                    3       41.2 ms
  inventory_update_lock                     2       49.8 ms
  payment_gateway_sync                      2       36.5 ms

PREDICTED CONTENTION RISK
──────────────────────────────────────────────────────────────────────
  Risk Level: MEDIUM
  Confidence: LOW=15.2%  MEDIUM=68.3%  HIGH=16.5%

──────────────────────────────────────────────────────────────────────
  Press Ctrl+C to stop monitoring
```

## Technical Decisions

### Why Simulated Data?

- **Portability**: Works without kernel hooks or instrumentation
- **Reproducibility**: Consistent results for development and testing
- **Safety**: No risk of interfering with real system locks
- **Flexibility**: Easy to test edge cases and failure modes

In production, replace the simulator with real lock instrumentation (e.g., eBPF probes, DTrace, or OS-specific APIs).

### Why CLI Instead of Web UI?

- **Simplicity**: Fewer dependencies, easier deployment
- **Performance**: Lower overhead than web stack
- **DevOps-friendly**: Integrates with terminal-based workflows
- **Focus**: Emphasizes functionality over presentation

### Why Logistic Regression?

- **Explainability**: Can inspect feature coefficients
- **Speed**: Predictions in microseconds
- **Reliability**: Well-understood, battle-tested algorithm
- **Sufficient**: Achieves ~85% accuracy on test set

## Limitations and Future Work

### Current Limitations

1. **Simulated Data**: Not based on real lock behavior
   - Replace with actual kernel-level instrumentation (eBPF, SystemTap)
   
2. **No Temporal Dependencies**: Each window treated independently
   - Add LSTM or time-series model to capture trends
   
3. **Rule-Based Labels**: May miss complex contention patterns
   - Consider unsupervised learning or expert-labeled data
   
4. **Fixed Thresholds**: May not generalize across systems
   - Implement adaptive thresholding based on system profile
   
5. **Limited Features**: Only 5 metrics
   - Add: lock type, holder thread, lock hierarchy, CPU utilization

### Future Enhancements

**Short-term:**
- Add historical trend visualization
- Implement alerting thresholds
- Export metrics to time-series database (Prometheus, InfluxDB)
- Add lock dependency graph visualization

**Long-term:**
- Real kernel instrumentation (eBPF probes)
- Multi-system monitoring with centralized dashboard
- Anomaly detection for unexpected contention patterns
- Integration with profiling tools (perf, gdb)
- Automatic remediation suggestions

## Project Structure

```
.
├── scripts/
│   ├── generate_dataset.py      # Dataset generation
│   ├── train_model.py            # ML model training
│   ├── predict.py                # Prediction wrapper
│   ├── cli_monitor.py            # Terminal dashboard
│   └── run_complete_system.py   # Orchestrator
├── lock_contention_dataset.csv   # Generated dataset
├── model.pkl                     # Trained model
├── scaler.pkl                    # Feature scaler
├── model_metadata.pkl            # Label encoder & metadata
└── README.md                     # This file
```

## Performance Characteristics

- **Dataset Generation**: ~0.5s for 1000 samples
- **Model Training**: ~1s on CPU
- **Prediction Latency**: <1ms per prediction
- **Dashboard Refresh**: 2s default (configurable)
- **Memory Usage**: <50MB total

## Academic Context

This project demonstrates:
- **Systems Engineering**: Monitoring architecture, data collection
- **Machine Learning**: Classification, feature engineering, evaluation
- **Software Engineering**: Clean code, modular design, CLI tools
- **Practical Constraints**: Working within realistic limitations

Suitable for:
- Systems programming coursework
- ML applications projects
- Performance monitoring studies
- DevOps automation examples

## License

This is an academic project template. Adapt freely for your needs.

## Support

For issues or questions, refer to the inline code comments or modify the system to fit your requirements.
