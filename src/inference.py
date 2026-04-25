"""
Inference module for Predictive Maintenance
Handles data preprocessing, feature engineering, and predictions
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceModel:
    """
    Wrapper class for predictive maintenance model
    In production, this would load the trained LSTM model
    For demo purposes, uses rule-based predictions
    """
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.seq_len = 30
        self.model = None
        self.use_lstm = False
        self._load_artifacts()

    def _load_artifacts(self):
        """Try to load trained LSTM artifacts from the project models folder."""
        base_dir = os.path.dirname(__file__)
        model_path = os.path.abspath(os.path.join(base_dir, '..', 'models', 'lstm_rul_model.keras'))
        scaler_path = os.path.abspath(os.path.join(base_dir, '..', 'models', 'lstm_scaler.pkl'))

        if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
            print("⚠️ Falling back to rule-based (model files not found)")
            return

        try:
            import tensorflow as tf

            self.model = tf.keras.models.load_model(model_path)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            self.use_lstm = True
            print("✅ Loaded trained LSTM model")
        except (ImportError, OSError, ValueError, RuntimeError, pickle.PickleError) as exc:
            self.model = None
            self.use_lstm = False
            print(f"⚠️ Falling back to rule-based (failed to load model: {exc})")

    def _predict_with_lstm(self, data_processed):
        """Run inference with trained LSTM model if artifacts are available."""
        base_feature_cols = [
            c for c in data_processed.columns
            if c.startswith('sensor_') or c.startswith('setting_')
        ]

        if not base_feature_cols:
            raise ValueError("No sensor/setting columns found for LSTM inference")

        expected_cols = getattr(self.scaler, 'feature_names_in_', None)
        if expected_cols is not None:
            expected_cols = list(expected_cols)
            input_df = data_processed.reindex(columns=expected_cols, fill_value=0)
        else:
            input_df = data_processed[base_feature_cols]

        scaled = self.scaler.transform(input_df)
        input_shape = getattr(self.model, 'input_shape', None)
        shape = tuple(input_shape) if isinstance(input_shape, (tuple, list)) else ()

        # Most sequence models are (batch, timesteps, features).
        if len(shape) == 3:
            timesteps = int(shape[1]) if shape[1] is not None else self.seq_len
            features = int(shape[2]) if shape[2] is not None else scaled.shape[1]

            seq = scaled[-timesteps:]
            if seq.shape[0] < timesteps:
                pad_rows = timesteps - seq.shape[0]
                pad = np.zeros((pad_rows, seq.shape[1]))
                seq = np.vstack([pad, seq])

            if seq.shape[1] < features:
                pad_cols = features - seq.shape[1]
                seq = np.hstack([seq, np.zeros((seq.shape[0], pad_cols))])
            elif seq.shape[1] > features:
                seq = seq[:, :features]

            model_input = np.expand_dims(seq, axis=0)
        else:
            model_input = np.expand_dims(scaled[-1], axis=0)

        pred = self.model.predict(model_input, verbose=0)
        pred_val = float(np.asarray(pred).reshape(-1)[0])

        predicted_rul = max(5.0, pred_val)
        confidence_interval = max(8.0, predicted_rul * 0.20)

        if predicted_rul < 30:
            status = "CRITICAL"
            recommendation = "Schedule maintenance immediately (within 5 flights)"
            potential_savings = 285000
        elif predicted_rul < 60:
            status = "WARNING"
            recommendation = "Schedule maintenance soon (within 10-15 flights)"
            potential_savings = 285000
        else:
            status = "HEALTHY"
            recommendation = "Continue normal operations. Next scheduled maintenance."
            potential_savings = 0

        model_confidence = min(95, max(70, 100 - (confidence_interval / predicted_rul * 100)))

        return {
            'predicted_rul': predicted_rul,
            'confidence_interval': confidence_interval,
            'status': status,
            'recommendation': recommendation,
            'potential_savings': potential_savings,
            'model_confidence': model_confidence,
            'degradation_score': 100 - predicted_rul,
        }

    def _predict_rule_based(self, data_processed):
        """Fallback prediction used when trained artifacts are unavailable."""
        # Get last 30 cycles for prediction
        last_cycles = data_processed.tail(30)

        # Rule-based prediction (demo version)
        # In production, this would use the trained LSTM model

        # Extract key sensor trends
        sensor_cols = [c for c in last_cycles.columns if c.startswith('sensor_')]

        # Calculate degradation indicators
        temp_trend = 0
        vibration_trend = 0
        pressure_trend = 0

        if 'sensor_4' in last_cycles.columns:
            temp_trend = last_cycles['sensor_4'].iloc[-1] - last_cycles['sensor_4'].iloc[0]

        if 'sensor_7' in last_cycles.columns:
            vibration_trend = last_cycles['sensor_7'].iloc[-1] - last_cycles['sensor_7'].iloc[0]

        if 'sensor_11' in last_cycles.columns:
            pressure_trend = last_cycles['sensor_11'].iloc[-1] - last_cycles['sensor_11'].iloc[0]

        # Calculate variation (higher variation = more degradation)
        variations = []
        for col in sensor_cols[:10]:  # Use first 10 sensors
            if col in last_cycles.columns:
                variations.append(last_cycles[col].std())

        avg_variation = np.mean(variations) if variations else 0.5

        # Predict RUL based on trends and variations
        # Higher trends and variations = lower RUL
        base_rul = 100

        # Adjust based on temperature trend
        if temp_trend > 5:
            base_rul -= 30
        elif temp_trend > 2:
            base_rul -= 15

        # Adjust based on vibration
        if vibration_trend > 0.05:
            base_rul -= 25
        elif vibration_trend > 0.02:
            base_rul -= 10

        # Adjust based on variation
        if avg_variation > 1.0:
            base_rul -= 20
        elif avg_variation > 0.5:
            base_rul -= 10

        # Pressure instability is another degradation signal.
        if pressure_trend > 0.5:
            base_rul -= 10

        # Ensure RUL is positive
        predicted_rul = max(5, base_rul)

        # Calculate confidence interval
        confidence_interval = max(8, predicted_rul * 0.20)  # 20% of RUL

        # Determine status
        if predicted_rul < 30:
            status = "CRITICAL"
            recommendation = "Schedule maintenance immediately (within 5 flights)"
            potential_savings = 285000
        elif predicted_rul < 60:
            status = "WARNING"
            recommendation = "Schedule maintenance soon (within 10-15 flights)"
            potential_savings = 285000
        else:
            status = "HEALTHY"
            recommendation = "Continue normal operations. Next scheduled maintenance."
            potential_savings = 0

        # Calculate model confidence (how certain we are)
        model_confidence = min(95, max(70, 100 - (confidence_interval / predicted_rul * 100)))

        return {
            'predicted_rul': predicted_rul,
            'confidence_interval': confidence_interval,
            'status': status,
            'recommendation': recommendation,
            'potential_savings': potential_savings,
            'model_confidence': model_confidence,
            'degradation_score': 100 - predicted_rul,  # Higher = more degraded
        }
        
    def create_rolling_features(self, df, window=5):
        """Create rolling window features"""
        df_roll = df.copy()
        sensors = [c for c in df.columns if c.startswith('sensor_')]
        
        for s in sensors:
            df_roll[f'{s}_rmean'] = df_roll[s].rolling(window, min_periods=1).mean()
            df_roll[f'{s}_rstd'] = df_roll[s].rolling(window, min_periods=1).std().fillna(0)
            df_roll[f'{s}_rmin'] = df_roll[s].rolling(window, min_periods=1).min()
            df_roll[f'{s}_rmax'] = df_roll[s].rolling(window, min_periods=1).max()
            df_roll[f'{s}_trend'] = df_roll[s].diff(window).fillna(0)
        
        return df_roll
    
    def predict(self, data):
        """
        Make RUL prediction on engine data
        
        Args:
            data: DataFrame with sensor readings (minimum 30 cycles)
            
        Returns:
            dict with prediction results
        """
        
        # Feature engineering
        data_processed = self.create_rolling_features(data)

        if self.use_lstm and self.model is not None:
            try:
                return self._predict_with_lstm(data_processed)
            except (ValueError, TypeError, RuntimeError) as exc:
                # Keep dashboard usable even if model input shape mismatches runtime data.
                print(f"⚠️ Falling back to rule-based (LSTM prediction failed: {exc})")

        return self._predict_rule_based(data_processed)


def generate_example_data(num_cycles=50, health_status='healthy'):
    """
    Generate synthetic engine sensor data for demo purposes
    
    Args:
        num_cycles: Number of flight cycles to generate
        health_status: 'healthy', 'degrading', or 'critical'
        
    Returns:
        DataFrame with synthetic sensor readings
    """
    
    np.random.seed(42)
    
    # Base sensor values (typical operating conditions)
    base_values = {
        'sensor_1': 518.67,
        'sensor_2': 642.50,
        'sensor_3': 1585.0,
        'sensor_4': 1398.0,
        'sensor_5': 14.62,
        'sensor_6': 21.61,
        'sensor_7': 554.5,
        'sensor_8': 2388.0,
        'sensor_9': 9050.0,
        'sensor_10': 1.30,
        'sensor_11': 47.50,
        'sensor_12': 521.70,
        'sensor_13': 2388.0,
        'sensor_14': 8138.0,
        'sensor_15': 8.48,
        'sensor_16': 0.03,
        'sensor_17': 392.0,
        'sensor_18': 2388.0,
        'sensor_19': 100.0,
        'sensor_20': 39.05,
        'sensor_21': 23.42,
    }
    
    # Settings (operating conditions)
    settings = {
        'setting_1': 0.0007,
        'setting_2': 0.0004,
        'setting_3': 100.0,
    }
    
    data = []
    
    for cycle in range(num_cycles):
        row = {'cycle': cycle + 1}
        
        # Add settings
        for key, val in settings.items():
            row[key] = val + np.random.normal(0, val * 0.01)
        
        # Add sensors with degradation patterns
        for sensor, base_val in base_values.items():
            
            if health_status == 'healthy':
                # Minimal variation, no trend
                noise = np.random.normal(0, base_val * 0.01)
                trend = 0
                
            elif health_status == 'degrading':
                # Moderate variation, slight upward trend
                noise = np.random.normal(0, base_val * 0.02)
                trend = (cycle / num_cycles) * base_val * 0.05
                
            else:  # critical
                # High variation, strong upward trend
                noise = np.random.normal(0, base_val * 0.05)
                trend = (cycle / num_cycles) * base_val * 0.15
                
                # Add occasional spikes
                if cycle > num_cycles * 0.7 and np.random.random() < 0.2:
                    noise += base_val * 0.10
            
            row[sensor] = base_val + trend + noise
        
        data.append(row)
    
    df = pd.DataFrame(data)
    return df


# For testing
if __name__ == "__main__":
    # Test with healthy engine
    print("Testing with healthy engine...")
    data_healthy = generate_example_data(50, 'healthy')
    model = PredictiveMaintenanceModel()
    result = model.predict(data_healthy)
    print(f"RUL: {result['predicted_rul']:.0f} ± {result['confidence_interval']:.0f} cycles")
    print(f"Status: {result['status']}")
    
    # Test with critical engine
    print("\nTesting with critical engine...")
    data_critical = generate_example_data(50, 'critical')
    result = model.predict(data_critical)
    print(f"RUL: {result['predicted_rul']:.0f} ± {result['confidence_interval']:.0f} cycles")
    print(f"Status: {result['status']}")
