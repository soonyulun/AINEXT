from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np
from io import BytesIO
import base64
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

app = Flask(__name__)

# --- Technical Indicators ---
def calculate_ema(data, window):
    return data['Close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data):
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def predict_future_prices(data, days=10):
    recent_data = data['Close'].tail(30).values.reshape(-1, 1)
    X = np.arange(len(recent_data)).reshape(-1, 1)
    y = recent_data
    
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    future_days = np.arange(len(recent_data), len(recent_data) + days).reshape(-1, 1)
    predictions = model.predict(future_days)
    
    return predictions.flatten(), r2

def get_stock_data(ticker):
    try:
        data = yf.download(ticker, period="2y")
        if len(data) < 400:
            return None, None, None
        
        data['EMA_50'] = calculate_ema(data, 50)
        data['SMA_200'] = data['Close'].rolling(200).mean()
        data['RSI'] = calculate_rsi(data)
        data['MACD'], data['Signal'] = calculate_macd(data)
        
        future_prices, r2_score = predict_future_prices(data, 20)
        return data.dropna(), future_prices, r2_score
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def create_plot(stock_data, future_prices):
    fig = Figure(figsize=(12, 14))
    
    # Price plot
    ax0 = fig.add_subplot(4, 1, 1)
    ax0.plot(stock_data.index, stock_data['Close'], label='Price', color='blue')
    ax0.plot(stock_data.index, stock_data['EMA_50'], label='50-EMA', color='orange')
    ax0.plot(stock_data.index, stock_data['SMA_200'], label='200-SMA', color='red')
    
    # RSI plot
    ax1 = fig.add_subplot(4, 1, 2)
    ax1.plot(stock_data.index, stock_data['RSI'], label='RSI(14)', color='purple')
    ax1.axhline(70, color='red', linestyle='--')
    ax1.axhline(30, color='green', linestyle='--')
    
    # MACD plot
    ax2 = fig.add_subplot(4, 1, 3)
    ax2.plot(stock_data.index, stock_data['MACD'], label='MACD', color='blue')
    ax2.plot(stock_data.index, stock_data['Signal'], label='Signal', color='red')
    
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker']
        stock_data, future_prices, r2_score = get_stock_data(ticker)
        
        if stock_data is not None:
            latest_close = float(stock_data['Close'].iloc[-1])
            ema_50 = float(stock_data['EMA_50'].iloc[-1])
            sma_200 = float(stock_data['SMA_200'].iloc[-1])
            current_rsi = float(stock_data['RSI'].iloc[-1])
            current_macd = float(stock_data['MACD'].iloc[-1])
            current_signal = float(stock_data['Signal'].iloc[-1])
            
            if len(future_prices) > 0:
                predicted_price = future_prices[-1]
                price_change = (predicted_price - latest_close) / latest_close * 100
            else:
                predicted_price = latest_close
                price_change = 0
            
            plot_url = create_plot(stock_data, future_prices)
            
            return render_template('index.html', 
                                ticker=ticker,
                                plot_url=plot_url,
                                latest_close=latest_close,
                                predicted_price=predicted_price,
                                price_change=price_change,
                                r2_score=r2_score,
                                current_rsi=current_rsi,
                                current_macd=current_macd,
                                current_signal=current_signal,
                                ema_50=ema_50,
                                sma_200=sma_200,
                                analysis_complete=True)
    
    return render_template('index.html', analysis_complete=False)

if __name__ == "__main__":
    app.run(debug=True)
