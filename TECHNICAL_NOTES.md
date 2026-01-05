# Technical Implementation Notes

Detailed technical decisions and implementation specifics for the lock contention monitoring system.

## Dataset Generation

### Statistical Distributions Used

**Normal Operation (Gamma Distribution)**
\`\`\`python
avg_wait = np.random.gamma(shape=2, scale=5)
# Shape=2, Scale=5 → Mean=10, Variance=50
# Produces realistic right-skewed distribution
\`\`\`

**Blocked Thread Percentage (Beta Distribution)**
\`\`\`python
blocked_pct = np.random.beta(alpha=2, beta=10) * 20
# Alpha=2, Beta=10 → Skewed toward low values
# Scaled to 0-20% range for normal operation
\`\`\`

**Contention Frequency (Poisson Distribution)**
\`\`\`python
frequency = np.random.poisson(lambda=5)
# Lambda=5 → Expected 5 events per window
# Discrete count distribution
\`\`\`

### Why These Distributions?

- **Gamma**: Models wait times (always positive, right-skewed)
- **Beta**: Models percentages (bounded 0-1, flexible shape)
- **Poisson**: Models event counts (discrete, memoryless arrivals)

## ML Model Training

### Feature Standardization

\`\`\`python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
# Transforms: X' = (X - mean) / std
\`\`\`

**Impact:**
- Prevents large-magnitude features from dominating
- Improves convergence speed
- Required for distance-based algorithms

### Logistic Regression Configuration

\`\`\`python
LogisticRegression(
    max_iter=1000,           # Sufficient for convergence
    random_state=42,         # Reproducibility
    multi_class='ovr',       # One-vs-Rest strategy
    C=1.0                    # L2 regularization strength
)
\`\`\`

**Multi-class Strategy:**
- One-vs-Rest: Trains 3 binary classifiers (HIGH vs rest, MEDIUM vs rest, LOW vs rest)
- Alternative: Multinomial (single softmax classifier) - similar performance here

**Regularization (C=1.0):**
- C = inverse regularization strength
- Lower C → stronger regularization → simpler model
- C=1.0 is standard default, works well for this problem

### Train/Test Split

\`\`\`python
train_test_split(X, y, test_size=0.2, stratify=y)
\`\`\`

- 80/20 split: Industry standard for medium datasets
- Stratified: Maintains class distribution in both sets
- Critical with imbalanced data (10% HIGH, 30% MEDIUM, 60% LOW)

## CLI Dashboard Implementation

### Terminal Clearing

\`\`\`python
os.system('clear' if os.name != 'nt' else 'cls')
\`\`\`

- `os.name == 'nt'`: Windows detection
- `clear`: Unix/Linux/Mac terminal command
- `cls`: Windows command prompt command

### ANSI Color Codes

\`\`\`python
RED = '\033[91m'
RESET = '\033[0m'
\`\`\`

- ANSI escape sequences for terminal colors
- `\033[` starts escape sequence
- `91m` = bright red color code
- `0m` = reset to default

### Metric Color Coding

\`\`\`python
def _get_metric_color(value, warn_threshold, critical_threshold):
    if value >= critical_threshold:
        return Colors.RED
    elif value >= warn_threshold:
        return Colors.YELLOW
    return Colors.GREEN
\`\`\`

**Thresholds chosen based on:**
- Normal operation: < 50ms avg wait
- Warning: 50-150ms avg wait
- Critical: > 150ms avg wait

## Simulated Monitoring Dynamics

### Temporal Evolution

\`\`\`python
# Gradual drift
base_multiplier = np.random.uniform(0.9, 1.1)

# Periodic spike (every 5 iterations)
if iteration % 5 == 0:
    base_multiplier = np.random.uniform(1.2, 2.0)

# Relief event (every 20 iterations)
if iteration % 20 == 0:
    base_multiplier = np.random.uniform(0.3, 0.6)
\`\`\`

**Simulates realistic patterns:**
- Gradual system load increases
- Periodic traffic spikes
- Deployment/restart relief events

### Lock Distribution (Pareto)

\`\`\`python
weights = np.random.pareto(2, size=5) + 1
weights = weights / weights.sum()
\`\`\`

**Why Pareto?**
- Models "80/20 rule": Few locks cause most contention
- Shape parameter = 2: Moderate skew
- +1 shift: Ensures positive weights

## Model Persistence

### Pickle Format

\`\`\`python
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
\`\`\`

**Alternatives:**
- joblib: Better for large numpy arrays
- ONNX: Cross-platform deployment
- TensorFlow SavedModel: Deep learning standard

**Chosen pickle because:**
- Simple, built-in
- Small model size (<1MB)
- Python-only deployment target

## Performance Optimization

### Prediction Speed

\`\`\`python
features_scaled = scaler.transform(features)  # ~10μs
prediction = model.predict(features_scaled)    # ~100μs
probabilities = model.predict_proba(features)  # ~200μs
\`\`\`

Total prediction time: <1ms (suitable for real-time)

### Dashboard Refresh Strategy

\`\`\`python
time.sleep(interval)  # Default: 2 seconds
\`\`\`

**Trade-offs:**
- Faster: More responsive, higher CPU usage
- Slower: Lower overhead, may miss transient spikes

2 seconds chosen as balance for human monitoring.

## Error Handling

### Graceful Degradation

\`\`\`python
try:
    self.predictor = ContentionPredictor()
    return True
except FileNotFoundError:
    print("Warning: Model not found...")
    return False
\`\`\`

Monitor continues without predictions if model unavailable.

### Keyboard Interrupt

\`\`\`python
except KeyboardInterrupt:
    print("Monitoring stopped.")
    sys.exit(0)
\`\`\`

Clean exit on Ctrl+C (standard Unix behavior).

## Code Organization

### Separation of Concerns

1. **generate_dataset.py**: Pure data generation logic
2. **train_model.py**: Pure ML training logic
3. **predict.py**: Prediction wrapper (no CLI dependencies)
4. **cli_monitor.py**: UI/display only

**Benefits:**
- Easy testing (can test each module independently)
- Reusable components (predict.py can be imported elsewhere)
- Clear responsibilities

### Class Design

\`\`\`python
class ContentionPredictor:
    def __init__(self, model_path, scaler_path, metadata_path):
        # Load resources once
        
    def predict(self, metrics):
        # Pure function: metrics → prediction
\`\`\`

**Design principles:**
- Encapsulation: Hide internal model details
- Single responsibility: Only prediction
- Dependency injection: Paths configurable

## Testing Strategy

### Manual Testing

\`\`\`python
if __name__ == '__main__':
    # Test code at module level
    predictor = ContentionPredictor()
    test_metrics = {...}
    risk, probs = predictor.predict(test_metrics)
    print(f"Test prediction: {risk}")
\`\`\`

Each module has `__main__` test block.

### Production Testing

**Recommended additions:**
- Unit tests: pytest for each function
- Integration tests: Full pipeline end-to-end
- Smoke tests: Quick sanity checks
- Load tests: Monitor performance under stress

## Security Considerations

### Pickle Safety

\`\`\`python
with open(model_path, 'rb') as f:
    model = pickle.load(f)
\`\`\`

**Warning:** pickle can execute arbitrary code
- Only load models from trusted sources
- Consider joblib for better safety
- Use ONNX for production deployments

### Input Validation

**Current implementation:** No input validation

**Production requirements:**
- Validate metric ranges (e.g., wait_time >= 0)
- Check for NaN/Inf values
- Rate limiting on prediction requests
- Sanitize any user-provided paths

## Scalability Considerations

### Current Limitations

- Single-process monitoring
- In-memory data only
- No persistence between runs
- No distributed monitoring

### Scale-up Strategy

1. **Multi-process**: Monitor multiple applications
2. **Centralized storage**: Time-series database (Prometheus)
3. **Distributed tracing**: Correlate locks across services
4. **Stream processing**: Apache Kafka + real-time ML

## Deployment Scenarios

### Development

\`\`\`bash
python scripts/run_complete_system.py
\`\`\`

### Production (Hypothetical)

\`\`\`bash
# Background monitoring with logging
python scripts/cli_monitor.py --interval 5 > logs/monitor.log 2>&1 &

# Systemd service
[Unit]
Description=Lock Contention Monitor

[Service]
ExecStart=/usr/bin/python3 /opt/monitor/cli_monitor.py
Restart=always
\`\`\`

### Docker (Future)

\`\`\`dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY scripts/ /app/scripts/
RUN pip install numpy pandas scikit-learn
CMD ["python", "scripts/run_complete_system.py"]
\`\`\`

## References

### Algorithms

- Logistic Regression: Bishop, "Pattern Recognition and Machine Learning"
- Feature Scaling: Géron, "Hands-On Machine Learning"

### Lock Contention

- Linux kernel docs: Documentation/locking/
- eBPF tools: iovisor/bcc repository
- DTrace guide: Gregg & Mauro, "DTrace: Dynamic Tracing"

### Terminal UI

- ANSI escape codes: Wikipedia, "ANSI escape code"
- Rich library (alternative): https://github.com/Textualize/rich

## Contribution Guidelines

If extending this project:

1. Maintain separation of concerns
2. Add docstrings to all functions
3. Keep dependencies minimal
4. Test on Linux/Mac/Windows
5. Document design decisions
6. Preserve defensive programming patterns
