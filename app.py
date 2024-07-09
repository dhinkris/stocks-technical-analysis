import streamlit as st
import yfinance as yf
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pandas_datareader.data as web
import os
from datetime import datetime, timedelta, date

# Set Streamlit page config to full screen
st.set_page_config(layout="wide")

# Function to fetch stock data and calculate technical indicators
def fetch_and_calculate(stock_symbol, start_date, end_date):
    stock_symbol = stock_symbol.split(':-:')[1]
    # Fetch stock data
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
    
    # Calculate RSI
    stock_data['RSI'] = ta.momentum.RSIIndicator(stock_data['Close']).rsi()
    
    # Calculate MACD
    macd = ta.trend.MACD(stock_data['Close'])
    stock_data['MACD'] = macd.macd()
    stock_data['MACD_Signal'] = macd.macd_signal()
    stock_data['MACD_Hist'] = macd.macd_diff()
    
    # Calculate Bollinger Bands
    bb = ta.volatility.BollingerBands(stock_data['Close'])
    stock_data['BB_High'] = bb.bollinger_hband()
    stock_data['BB_Low'] = bb.bollinger_lband()
    
    # Calculate Moving Averages
    stock_data['MA50'] = stock_data['Close'].rolling(window=50).mean()
    stock_data['MA200'] = stock_data['Close'].rolling(window=200).mean()
    
    return stock_data

# Function to provide buy, hold, or sell suggestion based on RSI and MACD
def get_suggestion(stock_data):
    suggestion=''
    if stock_data['RSI'].iloc[-1] > 70:
        suggestion+= "Sell (Overbought) | "
        color = "red"
    elif stock_data['RSI'].iloc[-1] < 30:
        suggestion+= "Buy (Oversold) | "
        color= "green"
    
    if stock_data['MACD'].iloc[-1] < stock_data['MACD_Signal'].iloc[-1]:
        suggestion+="Sell (MACD Bearish Crossover)"
        color = "red"
    elif stock_data['MACD'].iloc[-1] > stock_data['MACD_Signal'].iloc[-1]:
        suggestion+="Buy (MACD Bullish Crossover)"
        color = "green"
    if len(suggestion)==0:
        suggestion = "Hold"
        color = "yellow"
    return suggestion, color

# Get list of stock symbols (using a static list for this example)
def get_stock_symbols():
   # Check if the file exists and is not empty
    if not os.path.exists('symbols.txt') or os.stat('symbols.txt').st_size == 0:
        nasdaq = web.get_nasdaq_symbols()
        symbols = nasdaq.index.tolist()
        names = nasdaq['Security Name'].tolist()
        # Write symbols to a text file
        with open('symbols.txt', 'w') as file:
            for symbol, name in zip(symbols, names):
                try:
                    file.write(name+':-:'+symbol + '\n')
                except:
                    print("Unable to write:", symbol)
    else:
        # Read symbols from the text file if it exists and is not empty
        with open('symbols.txt', 'r') as file:
            symbols = [line.strip() for line in file.readlines()]
    return symbols

# Streamlit app
st.title("Stock Technical Analysis Dashboard")

# Function to calculate date range
def calculate_date_range(period):
    end_date = datetime.today()
    if period == "1W":
        start_date = end_date - timedelta(weeks=1)
    elif period == "1M":
        start_date = end_date - timedelta(weeks=4)
    elif period == "3M":
        start_date = end_date - timedelta(weeks=13)
    elif period == "YTD":
        start_date = datetime(end_date.year, 1, 1)
    elif period == "1Y":
        start_date = end_date - timedelta(weeks=52)
    elif period == "5Y":
        start_date = end_date - timedelta(weeks=260)
    return start_date, end_date

# Function to get suggestions for all time intervals
def get_all_suggestions(stock_symbol):
    periods = ["1W", "1M", "3M", "YTD", "1Y", "5Y"]
    suggestions = {}
    for period in periods:
        start_date, end_date = calculate_date_range(period)
        stock_data = fetch_and_calculate(stock_symbol, start_date, end_date)
        suggestion, color = get_suggestion(stock_data)
        suggestions[period] = {"suggestion": suggestion, "color": color}
    return suggestions


# Layout: selector on the left, plots on the right
col1, col2 = st.columns([1, 3])

with col1:
    stock_symbols = get_stock_symbols()
    stock_symbol = st.selectbox("Select a stock", stock_symbols)

    start_date = st.date_input("Start date", datetime(2023, 1, 1))
    end_date = st.date_input("End date", datetime.today())

    # period = st.selectbox("Select time period", ["1W", "1M", "3M", "YTD", "1Y", "5Y"])
    # start_date, end_date = calculate_date_range(period)

# Fetch data and calculate indicators
stock_data = fetch_and_calculate(stock_symbol, start_date, end_date)
# Display suggestions for all time intervals
suggestions = get_all_suggestions(stock_symbol)

with col2:
    # st.write(f"Suggestion: **{suggestion}**", unsafe_allow_html=True)
    # st.markdown(f"<h3 style='color: {color};'>{suggestion}</h3>", unsafe_allow_html=True)
    for period, result in suggestions.items():
        st.markdown(f"<h4>{period}: <span style='color: {result['color']};'>{result['suggestion']}</span></h4>", unsafe_allow_html=True)

    # Create subplots
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True,
                        vertical_spacing=0.02, subplot_titles=('Price with Bollinger Bands and Moving Averages', 
                                                               'MACD', 'RSI', 'Volume'))
    
    # Plot Price with Bollinger Bands and Moving Averages
    fig.add_trace(go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], 
                                 low=stock_data['Low'], close=stock_data['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['BB_High'], line=dict(color='blue', width=1), name='Bollinger High'), row=1, col=1)
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['BB_Low'], line=dict(color='blue', width=1), name='Bollinger Low'), row=1, col=1)
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA50'], line=dict(color='orange', width=1), name='MA50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA200'], line=dict(color='purple', width=1), name='MA200'), row=1, col=1)

    # Plot RSI
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], line=dict(color='black', width=1), name='RSI'), row=2, col=1)
    fig.add_shape(type='line', x0=stock_data.index[0], x1=stock_data.index[-1], y0=70, y1=70, line=dict(color='red', dash='dash'), row=2, col=1)
    fig.add_shape(type='line', x0=stock_data.index[0], x1=stock_data.index[-1], y0=30, y1=30, line=dict(color='green', dash='dash'), row=2, col=1)

    # Plot MACD
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MACD'], line=dict(color='blue', width=1), name='MACD'), row=1, col=2)
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MACD_Signal'], line=dict(color='red', width=1), name='MACD Signal'), row=1, col=2)
    fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['MACD_Hist'], name='MACD Histogram'), row=1, col=2)

    # Plot Volume
    fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Volume'), row=2, col=2)

    fig.update_layout(height=800, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
