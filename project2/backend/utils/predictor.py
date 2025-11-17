# backend/utils/predictor.py
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def prepare_new_data(df_close):
    """
    df_close: DataFrame with single 'Close' column and Date index
    Returns: last_60 shaped (1,60,1) and the fitted scaler
    """
    data = df_close[["Close"]].values.astype(float)  # shape (n,1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(data)  # fits to the current ticker
    if len(scaled) < 60:
        raise ValueError("not enough data (need at least 60 rows)")
    last_60 = scaled[-60:].reshape(1, 60, 1)
    return last_60, scaler

def predict_next_30(model, last_60, scaler):
    """
    model: compiled keras model
    last_60: np array shape (1,60,1)
    scaler: fitted MinMaxScaler
    Returns: numpy array of 30 predicted prices (inverse transformed)
    """
    preds = []
    temp = last_60.copy()  # shape (1,60,1)
    for _ in range(30):
        yhat = model.predict(temp, verbose=0)  # shape (1,1)
        val = float(yhat[0, 0])
        preds.append(val)
        # reshape to (1,1,1) and append
        yhat_3d = np.array(val).reshape(1, 1, 1)
        temp = np.append(temp[:, 1:, :], yhat_3d, axis=1)  # keeps shape (1,60,1)
    preds = np.array(preds).reshape(-1, 1)
    inv = scaler.inverse_transform(preds).reshape(-1)
    return inv
