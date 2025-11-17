# streamlit_stock_dashboard.py

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

st.title("📈 Stock Analysis Dashboard")
st.markdown("Enter a stock ticker symbol and select a date range to view analysis.")

# --- User Inputs ---
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, MSFT):", value="AAPL")
start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", pd.to_datetime("2023-11-17"))

# --- Fetch Data ---
if ticker:
    data = yf.download(ticker, start=start_date, end=end_date)
    
    if data.empty:
        st.error("No data found for this ticker or date range.")
    else:
        # --- Calculate Indicators ---
        data['MA100'] = data['Close'].rolling(window=100).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()

        # RSI
        delta = data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -1*delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # --- Display Summary ---
        st.subheader("📊 Summary Statistics")
        st.dataframe(data.describe().T)

        st.subheader("📋 Min/Max/Total Volume")
        summary = {
            'Open_min': data['Open'].min(),
            'Open_max': data['Open'].max(),
            'Close_min': data['Close'].min(),
            'Close_max': data['Close'].max(),
            'High_min': data['High'].min(),
            'High_max': data['High'].max(),
            'Low_min': data['Low'].min(),
            'Low_max': data['Low'].max(),
            'Volume_total': data['Volume'].sum()
        }
        st.dataframe(pd.DataFrame([summary]))

        # --- Plot Chart ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.1, row_heights=[0.7, 0.3])

        # Top Panel: Candlestick + MA100 + MA200
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'], name='Candlestick'), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MA100'], line=dict(color='blue', width=1), name='MA100'), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MA200'], line=dict(color='orange', width=1), name='MA200'), row=1, col=1)

        # Bottom Panel: RSI
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='red', width=1), name='RSI'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="grey", row=2, col=1)  # Overbought line
        fig.add_hline(y=30, line_dash="dash", line_color="grey", row=2, col=1)  # Oversold line

        fig.update_layout(title=f'{ticker} Stock Analysis: MA100, MA200 & RSI',
                          yaxis_title='Price',
                          xaxis_title='Date',
                          height=800)

        st.plotly_chart(fig, use_container_width=True)
