"""
Cross-Platform Contention Normalization Layer
Maps OS-specific metrics to platform-independent contention indicators
"""

import numpy as np
from typing import Dict, Tuple
from enum import Enum

class Platform(Enum):
    """Supported platforms with different observability levels"""
    LINUX_EBPF = "linux_ebpf"      # High precision, kernel-level
    WINDOWS_PSUTIL = "windows_psutil"  # Inferred, process-level
    SYNTHETIC = "synthetic"        # Simulated for training

class DataConfidence(Enum):
    """Data quality levels based on collection method"""
    HIGH = 0.95      # eBPF direct measurement
    MEDIUM = 0.70    # psutil inference with validation
    LOW = 0.50       # psutil inference without validation
    SYNTHETIC = 0.85 # Simulated data (known ground truth)

class ContentionNormalizer:
    """
    Normalizes platform-specific metrics into common contention indicators.
    
    Design principle: Raw OS metrics NEVER reach ML model directly.
    All inputs must pass through this normalization layer.
    """
    
    def __init__(self):
        # Normalization bounds for each platform
        self.linux_bounds = {
            'wait_time_ns': (0, 1_000_000_000),  # 0-1000ms in nanoseconds
            'frequency': (0, 100),
            'blocked_pct': (0, 100),
        }
        
        self.windows_bounds = {
            'thread_wait_ratio': (0, 1),
            'io_wait_pct': (0, 100),
            'handle_contention': (0, 1000),
        }
    
    def normalize_linux_ebpf(self, raw_metrics: Dict) -> Tuple[Dict, float]:
        """
        Normalize Linux eBPF metrics to platform-independent indicators.
        
        Args:
            raw_metrics: {
                'avg_wait_time_ns': nanoseconds,
                'max_wait_time_ns': nanoseconds,
                'lock_frequency': count,
                'blocked_thread_count': count,
                'total_threads': count
            }
        
        Returns:
            (normalized_indicators, confidence_score)
        """
        # Convert nanoseconds to milliseconds for normalization
        avg_wait_ms = raw_metrics.get('avg_wait_time_ns', 0) / 1_000_000
        max_wait_ms = raw_metrics.get('max_wait_time_ns', 0) / 1_000_000
        
        # Calculate blocked percentage
        blocked = raw_metrics.get('blocked_thread_count', 0)
        total = raw_metrics.get('total_threads', 1)
        blocked_pct = (blocked / total) * 100 if total > 0 else 0
        
        # Normalize to 0-1 scale
        indicators = {
            'lock_pressure': self._normalize(avg_wait_ms, 0, 200),  # 0-200ms range
            'blocking_severity': self._normalize(max_wait_ms, 0, 500),  # 0-500ms range
            'contention_frequency': self._normalize(raw_metrics.get('lock_frequency', 0), 0, 100),
            'thread_blocking_ratio': self._normalize(blocked_pct, 0, 100),
            'contention_trend': 0.0  # Requires historical data
        }
        
        # eBPF provides direct measurement - high confidence
        confidence = DataConfidence.HIGH.value
        
        return indicators, confidence
    
    def normalize_windows_psutil(self, raw_metrics: Dict) -> Tuple[Dict, float]:
        """
        Infer contention from Windows psutil metrics.
        
        IMPORTANT: This is INFERENCE, not direct measurement.
        Confidence is reduced due to indirect observation.
        
        Args:
            raw_metrics: {
                'num_threads': count,
                'threads_waiting': count (inferred from thread states),
                'io_wait_time': percentage,
                'open_handles': count,
                'ctx_switches': count
            }
        
        Returns:
            (normalized_indicators, confidence_score)
        """
        # Infer lock pressure from thread waiting ratio
        total_threads = raw_metrics.get('num_threads', 1)
        waiting_threads = raw_metrics.get('threads_waiting', 0)
        wait_ratio = waiting_threads / total_threads if total_threads > 0 else 0
        
        # Infer blocking severity from I/O wait
        io_wait = raw_metrics.get('io_wait_time', 0)
        
        # Infer contention frequency from context switches
        ctx_switches = raw_metrics.get('ctx_switches', 0)
        
        # Normalize to 0-1 scale
        indicators = {
            'lock_pressure': self._normalize(wait_ratio * 100, 0, 50),  # Inferred
            'blocking_severity': self._normalize(io_wait, 0, 100),  # Indirect
            'contention_frequency': self._normalize(ctx_switches, 0, 10000),  # Proxy
            'thread_blocking_ratio': self._normalize(wait_ratio * 100, 0, 100),
            'contention_trend': 0.0  # Requires historical data
        }
        
        # Determine confidence based on data quality
        # Lower confidence because we're inferring, not measuring
        if raw_metrics.get('has_thread_states', False):
            confidence = DataConfidence.MEDIUM.value  # Have thread state info
        else:
            confidence = DataConfidence.LOW.value  # Only basic metrics
        
        return indicators, confidence
    
    def normalize_synthetic(self, raw_metrics: Dict) -> Tuple[Dict, float]:
        """
        Normalize synthetic training data.
        
        Args:
            raw_metrics: {
                'avg_wait_time_ms': milliseconds,
                'max_wait_time_ms': milliseconds,
                'contention_frequency': count,
                'blocked_thread_percentage': percentage,
                'wait_time_growth_rate': ratio
            }
        
        Returns:
            (normalized_indicators, confidence_score)
        """
        indicators = {
            'lock_pressure': self._normalize(raw_metrics.get('avg_wait_time_ms', 0), 0, 200),
            'blocking_severity': self._normalize(raw_metrics.get('max_wait_time_ms', 0), 0, 500),
            'contention_frequency': self._normalize(raw_metrics.get('contention_frequency', 0), 0, 100),
            'thread_blocking_ratio': self._normalize(raw_metrics.get('blocked_thread_percentage', 0), 0, 100),
            'contention_trend': self._clip(raw_metrics.get('wait_time_growth_rate', 0), -2, 5)
        }
        
        # Synthetic data has known ground truth
        confidence = DataConfidence.SYNTHETIC.value
        
        return indicators, confidence
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if max_val == min_val:
            return 0.0
        normalized = (value - min_val) / (max_val - min_val)
        return np.clip(normalized, 0.0, 1.0)
    
    def _clip(self, value: float, min_val: float, max_val: float) -> float:
        """Clip value to range"""
        return np.clip(value, min_val, max_val)
    
    def get_feature_vector(self, indicators: Dict) -> np.ndarray:
        """
        Convert normalized indicators to ML feature vector.
        
        Feature order MUST match training data:
        [lock_pressure, blocking_severity, contention_frequency, 
         thread_blocking_ratio, contention_trend]
        """
        return np.array([
            indicators['lock_pressure'],
            indicators['blocking_severity'],
            indicators['contention_frequency'],
            indicators['thread_blocking_ratio'],
            indicators['contention_trend']
        ])
    
    def validate_indicators(self, indicators: Dict) -> bool:
        """Validate that all indicators are in valid range [0, 1] or defined bounds"""
        required_keys = ['lock_pressure', 'blocking_severity', 'contention_frequency',
                        'thread_blocking_ratio', 'contention_trend']
        
        if not all(k in indicators for k in required_keys):
            return False
        
        # Check ranges
        for key in required_keys[:4]:  # First 4 should be 0-1
            if not (0 <= indicators[key] <= 1):
                return False
        
        # contention_trend can be negative (declining contention)
        if not (-2 <= indicators['contention_trend'] <= 5):
            return False
        
        return True


class PlatformAwarePredictor:
    """
    Wrapper that adjusts prediction confidence based on data source platform.
    """
    
    def __init__(self, base_model, scaler, label_encoder):
        self.model = base_model
        self.scaler = scaler
        self.label_encoder = label_encoder
        self.normalizer = ContentionNormalizer()
    
    def predict_with_confidence(self, raw_metrics: Dict, platform: Platform) -> Tuple[str, Dict, float]:
        """
        Make platform-aware prediction with adjusted confidence.
        
        Returns:
            (risk_level, probabilities, data_confidence)
        """
        # Normalize based on platform
        if platform == Platform.LINUX_EBPF:
            indicators, data_confidence = self.normalizer.normalize_linux_ebpf(raw_metrics)
        elif platform == Platform.WINDOWS_PSUTIL:
            indicators, data_confidence = self.normalizer.normalize_windows_psutil(raw_metrics)
        else:  # SYNTHETIC
            indicators, data_confidence = self.normalizer.normalize_synthetic(raw_metrics)
        
        # Validate
        if not self.normalizer.validate_indicators(indicators):
            raise ValueError(f"Invalid indicators: {indicators}")
        
        # Get feature vector
        features = self.normalizer.get_feature_vector(indicators)
        
        # Scale and predict
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Get risk level
        risk_level = self.label_encoder.inverse_transform([prediction])[0]
        
        # Build probability dict
        prob_dict = {
            label: prob 
            for label, prob in zip(self.label_encoder.classes_, probabilities)
        }
        
        return risk_level, prob_dict, data_confidence
