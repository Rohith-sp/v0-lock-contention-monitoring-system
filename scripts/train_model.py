"""
Lock Contention Risk Prediction Model

Trains a lightweight ML model to predict lock contention risk levels.
Uses Logistic Regression for interpretability and speed.

Model Input: 5 contention metrics
Model Output: Risk level (LOW, MEDIUM, HIGH)

Design decisions:
- Logistic Regression: Fast, interpretable, sufficient for 3-class problem
- Standardization: Normalizes features for better convergence
- Train/test split: 80/20 for validation
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import os

def load_dataset(path: str = 'lock_contention_dataset.csv'):
    """Load the generated dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run generate_dataset.py first."
        )
    
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} samples from {path}")
    return df

def prepare_data(df: pd.DataFrame):
    """
    Prepare features and labels for training.
    
    Returns:
        X: Feature matrix
        y: Encoded labels (0=HIGH, 1=LOW, 2=MEDIUM)
        label_encoder: For converting predictions back to labels
        feature_names: List of feature column names
    """
    
    # Define feature columns
    feature_cols = [
        'avg_wait_time_ms',
        'max_wait_time_ms', 
        'contention_frequency',
        'blocked_thread_percentage',
        'wait_time_growth_rate'
    ]
    
    X = df[feature_cols].values
    y_labels = df['contention_risk_label'].values
    
    # Encode labels: HIGH=0, LOW=1, MEDIUM=2
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_labels)
    
    print(f"\nFeatures: {feature_cols}")
    print(f"Classes: {label_encoder.classes_}")
    
    return X, y, label_encoder, feature_cols

def train_model(X, y, label_encoder):
    """
    Train Logistic Regression model with standardization.
    
    Model choice rationale:
    - Logistic Regression: Linear decision boundaries work well for this problem
    - Multi-class: One-vs-Rest strategy
    - Regularization: L2 penalty prevents overfitting
    - Interpretable: Can inspect feature coefficients
    """
    
    # Split data: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Logistic Regression
    print("\nTraining Logistic Regression model...")
    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        multi_class='ovr',  # One-vs-Rest for multi-class
        C=1.0  # Regularization strength
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"\n=== Model Performance ===")
    print(f"Training accuracy: {train_score:.3f}")
    print(f"Test accuracy: {test_score:.3f}")
    
    # Detailed classification report
    y_pred = model.predict(X_test_scaled)
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=label_encoder.classes_))
    
    print(f"\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print(f"(Rows: actual, Columns: predicted)")
    
    return model, scaler

def save_model(model, scaler, label_encoder, feature_names,
               model_path='model.pkl', scaler_path='scaler.pkl',
               metadata_path='model_metadata.pkl'):
    """Save trained model, scaler, and metadata."""
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    metadata = {
        'label_encoder': label_encoder,
        'feature_names': feature_names,
        'classes': label_encoder.classes_.tolist()
    }
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    
    print(f"\n✓ Model saved to {model_path}")
    print(f"✓ Scaler saved to {scaler_path}")
    print(f"✓ Metadata saved to {metadata_path}")

def main():
    """Complete training pipeline."""
    
    # Load dataset
    df = load_dataset()
    
    # Prepare data
    X, y, label_encoder, feature_names = prepare_data(df)
    
    # Train model
    model, scaler = train_model(X, y, label_encoder)
    
    # Save artifacts
    save_model(model, scaler, label_encoder, feature_names)
    
    print("\n✓ Training complete!")
    print("\nModel limitations:")
    print("- Predictions based on dummy data, not real lock behavior")
    print("- Rule-based labels may not capture all contention patterns")
    print("- No temporal dependencies (each window independent)")
    print("- Threshold tuning required for production use")

if __name__ == '__main__':
    main()
