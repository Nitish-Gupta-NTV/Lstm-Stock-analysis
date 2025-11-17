# backend/app.py
import warnings
warnings.filterwarnings("ignore", message="Thread 'MainThread': missing ScriptRunContext")

import os
import json
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

import pandas as pd
import yfinance as yf
import numpy as np

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

from utils.predictor import prepare_new_data, predict_next_30

# --- logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

os.makedirs(DATA_DIR, exist_ok=True)
for f in (USERS_FILE, HISTORY_FILE):
    if not os.path.exists(f):
        with open(f, "w") as fp:
            json.dump({}, fp)

app = Flask(__name__)
CORS(app)

# ---------- helpers ----------
def load_users():
    with open(USERS_FILE, "r") as fp:
        try:
            return json.load(fp)
        except Exception:
            return {}

def save_users(users):
    with open(USERS_FILE, "w") as fp:
        json.dump(users, fp, indent=2)

def load_history():
    with open(HISTORY_FILE, "r") as fp:
        try:
            return json.load(fp)
        except Exception:
            return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as fp:
        json.dump(history, fp, indent=2)

# ---------- routes ----------
@app.get("/ping")
def ping():
    return jsonify({"status": "ok"}), 200

@app.post("/register")
def register():
    try:
        payload = request.get_json(force=True)
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", "")).strip()

        if not username or not password:
            return jsonify({"error": "username_and_password_required"}), 400

        users = load_users()
        if username in users:
            return jsonify({"error": "user_exists"}), 400

        users[username] = {"password": password}
        save_users(users)
        logger.info(f"User created: {username}")
        return jsonify({"ok": True, "message": "user_created"}), 201
    except Exception as e:
        logger.exception("Error in /register")
        return jsonify({"error": "server_error", "detail": str(e)}), 500

@app.post("/login")
def login():
    try:
        payload = request.get_json(force=True)
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", "")).strip()

        users = load_users()
        if username in users and users[username].get("password") == password:
            logger.info(f"Login success: {username}")
            return jsonify({"ok": True, "message": "login_successful"}), 200
        return jsonify({"error": "invalid_credentials"}), 401
    except Exception as e:
        logger.exception("Error in /login")
        return jsonify({"error": "server_error", "detail": str(e)}), 500

@app.post("/predict")
def predict():
    """
    Request JSON: { "ticker": "AAPL", "username": "optional_user" }
    Response JSON: { "ticker": "...", "predictions": [{date, price}, ...] }
    """
    try:
        payload = request.get_json(force=True)
        ticker = str(payload.get("ticker", "")).upper().strip()
        username = payload.get("username")

        if not ticker:
            return jsonify({"error": "ticker_required"}), 400

        # fetch data (3y gives enough history)
        try:
            df = yf.download(ticker, period="3y", interval="1d", progress=False)
        except Exception as e:
            logger.exception("yfinance failed")
            return jsonify({"error": "yfinance_failed", "detail": str(e)}), 500

        if df is None or df.empty or "Close" not in df.columns:
            return jsonify({"error": "no_data_for_ticker"}), 400

        df_close = df[["Close"]].dropna()
        if df_close.empty or len(df_close) < 80:
            return jsonify({"error": "not_enough_data"}), 400

        # prepare last_60 and scaler
        last_60, scaler = prepare_new_data(df_close)

        # Build quick model (same architecture as training)
        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=(60, 1)))
        model.add(LSTM(50))
        model.add(Dense(1))
        model.compile(loss="mse", optimizer="adam")

        # create dataset from full series and train briefly
        scaled_all = scaler.transform(df_close.values.astype(float))
        X_all = []
        y_all = []
        for i in range(60, len(scaled_all)):
            X_all.append(scaled_all[i-60:i, 0])
            y_all.append(scaled_all[i, 0])
        X_all = np.array(X_all).reshape(-1, 60, 1)
        y_all = np.array(y_all)

        # quick train (2 epochs)
        model.fit(X_all, y_all, epochs=2, batch_size=32, verbose=0)

        # predict next 30
        preds = predict_next_30(model, last_60, scaler)  # numpy array (30,)

        # build dates - use last valid index from df_close
        last_date = df_close.index[-1]
        dates = [(last_date + pd.Timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(30)]
        preds_list = [{"date": d, "price": float(round(float(p), 4))} for d, p in zip(dates, preds.tolist())]

        # save user history if username provided
        if username:
            history = load_history()
            user_hist = history.get(username, [])
            user_hist.append({
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": ticker,
                "predictions": preds_list
            })
            history[username] = user_hist
            save_history(history)

        return jsonify({"ticker": ticker, "predictions": preds_list}), 200

    except Exception as e:
        logger.exception("ERROR IN /predict")
        return jsonify({"error": "server_error", "detail": str(e)}), 500

@app.get("/history/<username>")
def get_history(username):
    try:
        history = load_history()
        return jsonify({"history": history.get(username, [])}), 200
    except Exception as e:
        logger.exception("Error in /history")
        return jsonify({"error": "server_error", "detail": str(e)}), 500

if __name__ == "__main__":
    # threaded=True helps handle concurrent front-end connections
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
