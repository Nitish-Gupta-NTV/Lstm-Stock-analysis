import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time
import yfinance as yf



# ----------------------------- API -----------------------------
API = "http://localhost:5000"
st.set_page_config(page_title="AI Stock Predictor", layout="wide")

# ----------------------------- CSS -----------------------------
st.markdown("""
<style>
body { background-color: #0D1117; }
.sidebar .sidebar-content { background-color: #0D1117 !important; }
.big-title {
    text-align: center; font-size: 42px; font-weight: bold;
    letter-spacing: 1px; color: #00E2FF; margin-top: -5px;
}
.card {
    background: rgba(255,255,255,0.05); padding: 20px;
    border-radius: 15px; color: white;
    box-shadow: 0px 0px 12px rgba(0,255,255,0.20);
}
input, textarea, .stTextInput { color: Black !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------- API Helper -----------------------------
def api_post(endpoint, payload):
    try:
        r = requests.post(f"{API}{endpoint}", json=payload, timeout=210)
        if r.status_code in (200, 201):
            return r.json(), None
        try:
            return None, r.json()
        except:
            return None, {"error": r.text}
    except Exception as e:
        return None, {"error": str(e)}

# ----------------------------- Graphs -----------------------------
def plot_prediction(df_pred, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_pred["date"], y=df_pred["price"],
        mode='lines+markers', name="Prediction", line=dict(width=3)
    ))
    fig.update_layout(template="plotly_dark",
                      title=f"{ticker} - 30 Day Prediction",
                      height=450)
    st.plotly_chart(fig, use_container_width=True)

def plot_history(df_hist, df_pred, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist["Date"], y=df_hist["Close"],
        mode='lines', name="Past Trend", line=dict(width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df_pred["date"], y=df_pred["price"],
        mode='lines+markers', name="Prediction", line=dict(width=3)
    ))
    fig.update_layout(template="plotly_dark",
                      title=f"{ticker} - Past 1 Year + Next 30 Days",
                      height=500)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------- Sidebar -----------------------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Go to:", [ "Signup","Login", "Dashboard", "History", "Profile"])

if "user" in st.session_state:
    st.sidebar.success(f"Logged in as: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ----------------------------- SIGNUP -----------------------------
if page == "Signup":
    st.markdown("<h1 class='big-title'>Create Account</h1>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    username = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        data, err = api_post("/register", {"username": username, "password": password})
        if data:
            st.success("Account created! Go to Login.")
        else:
            st.error(err.get("error"))
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- LOGIN -----------------------------
elif page == "Login":
    st.markdown("<h1 class='big-title'>AI Stock Predictor</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔐 Login")
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            data, err = api_post("/login", {"username": username, "password": password})
            if data:
                st.session_state["user"] = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(err.get("error"))
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- DASHBOARD -----------------------------
elif page == "Dashboard":
    
    if "user" not in st.session_state:
        st.warning("Login required")
        st.stop()

    st.markdown("<h1 class='big-title'>Dashboard</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        ticker_input = st.text_input("Enter Stock Symbol (AAPL, TSLA, INFY.NS, RELIANCE.NS)")
        if st.button("Predict"):
            ticker = ticker_input.strip().upper()
         #   if "." not in ticker and ticker.isalpha() and 2 <= len(ticker) <= 6:
          #      ticker = ticker + ".NS"  # Auto add NSE suffix

            st.info(f"Predicting for **{ticker}** ... Please wait ⏳")

            # --------- PREDICTION API CALL ----------
            data, err = api_post("/predict", {"ticker": ticker, "username": st.session_state["user"]})
            if data:
                preds = data["predictions"]
                df_pred = pd.DataFrame(preds)

                st.subheader("📅 Prediction Table")
                st.dataframe(df_pred, use_container_width=True)
                plot_prediction(df_pred, ticker)

                # --------- HISTORICAL DATA ----------
                st.subheader("📉 Past 1 Year + Prediction")

                @st.cache_data(ttl=3600)
                def get_history(ticker):
                    try:
                        df = yf.download(ticker, period="1y", interval="1d")
                        if df.empty:
                            return None
                        df = df[["Close"]].reset_index()
                        return df
                    except:
                        return None

                df_hist = get_history(ticker)

                if df_hist is None or df_hist.empty:
                    st.warning("Historical data not available. Using prediction as history.")
                    # Use prediction dates and prices as pseudo-history
                    df_hist = df_pred.copy()
                    df_hist.rename(columns={"date": "Date", "price": "Close"}, inplace=True)

                st.write(df_hist.head())  # Optional: debug
                plot_history(df_hist, df_pred, ticker)

            else:
                st.error(err.get("error"))

        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- HISTORY -----------------------------
elif page == "History":
    if "user" not in st.session_state:
        st.warning("Login required")
        st.stop()

    st.markdown("<h1 class='big-title'>Prediction History</h1>", unsafe_allow_html=True)
    r = requests.get(f"{API}/history/{st.session_state['user']}")
    if r.status_code == 200:
        history = r.json().get("history", [])
        if not history:
            st.info("No history available.")
        else:
            for item in reversed(history):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.write(f"**Ticker:** {item['ticker']} — {item['timestamp']}")
                df = pd.DataFrame(item["predictions"])
                st.dataframe(df, use_container_width=True)
                plot_prediction(df, item["ticker"])
                st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- PROFILE -----------------------------
elif page == "Profile":
    if "user" not in st.session_state:
        st.warning("Login required")
        st.stop()

    st.markdown("<h1 class='big-title'>👤 Profile</h1>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.write("**Username:**", st.session_state["user"])
    st.write("**Member Since:** Today 😎")
    st.write("**Predictions Made:** Unlimited 🚀")
    st.markdown("</div>", unsafe_allow_html=True)
