from flask import Flask, request
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

def generate_html(ticker=None, analysis_complete=False, **kwargs):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Stock Analysis Tool</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        form {{
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }}
        input[type="text"] {{
            padding: 10px;
            width: 200px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
        }}
        button {{
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #45a049;
        }}
        .results {{
            margin-top: 30px;
        }}
        .indicators {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .indicator {{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }}
        .indicator h3 {{
            margin-top: 0;
            color: #333;
        }}
        .chart {{
            margin-top: 20px;
            text-align: center;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .buy {{
            color: green;
            font-weight: bold;
        }}
        .sell {{
            color: red;
            font-weight: bold;
        }}
        .hold {{
            color: orange;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stock Analysis Tool</h1>
        <form method="POST">
            <input type="text" name="ticker" placeholder="Enter ticker (e.g. AAPL)" value="{ticker if ticker else 'BABA'}" required>
            <button type="submit">Analyze</button>
        </form>

        {f"""
        <div class="results">
            <h2>Analysis for {ticker}</h2>
            
            <div class="indicators">
                <div class="indicator">
                    <h3>Price Information</h3>
                    <p>Current Price: ${kwargs['latest_close']:.2f}</p>
                    <p>Predicted Price (20 days): ${kwargs['predicted_price']:.2f} ({kwargs['price_change']:.1f}%)</p>
                    <p>Model R² Score: {kwargs['r2_score']:.4f}</p>
                </div>
                
                <div class="indicator">
                    <h3>Technical Indicators</h3>
                    <p>RSI: {kwargs['current_rsi']:.1f}</p>
                    <p>MACD: {kwargs['current_macd']:.2f} ({'Bullish' if kwargs['current_macd'] > kwargs['current_signal'] else 'Bearish'})</p>
                    <p>Trend: {'Bullish' if kwargs['latest_close'] > kwargs['ema_50'] > kwargs['sma_200'] else 'Bearish'}</p>
                    <p>50EMA: ${kwargs['ema_50']:.2f}</p>
                    <p>200SMA: ${kwargs['sma_200']:.2f}</p>
                </div>
                
                <div class="indicator">
                    <h3>Trading Recommendation</h3>
                    {f"""
                    {f"""
                    <p class="{'buy' if kwargs['price_change'] > 5 else 'hold'}">🟢 STRONG BUY: Expected price increase of {kwargs['price_change']:.1f}% in 20 days</p>
                    """ if kwargs['price_change'] > 5 else ""}
                    {f"""
                    <p class="{'buy' if kwargs['price_change'] > 2 else 'hold'}">🟢 BUY: Expected price increase of {kwargs['price_change']:.1f}% in 20 days</p>
                    """ if 2 < kwargs['price_change'] <= 5 else ""}
                    {f"""
                    <p class="{'sell' if kwargs['price_change'] < -5 else 'hold'}">🔴 STRONG SELL: Expected price decrease of {-kwargs['price_change']:.1f}% in 20 days</p>
                    """ if kwargs['price_change'] < -5 else ""}
                    {f"""
                    <p class="{'sell' if kwargs['price_change'] < -2 else 'hold'}">🔴 SELL: Expected price decrease of {-kwargs['price_change']:.1f}% in 20 days</p>
                    """ if -5 <= kwargs['price_change'] < -2 else ""}
                    {f"""
                    <p class="hold">🟡 HOLD: Expected price movement within ±2% in 20 days</p>
                    """ if -2 <= kwargs['price_change'] <= 2 else ""}
                    """ if kwargs['r2_score'] > 0.4 else """
                    <p class="hold">⚠️ Low model confidence - using standard technical analysis</p>
                    {f"""
                    <p class="{'buy' if kwargs['latest_close'] > kwargs['ema_50'] > kwargs['sma_200'] else 'sell' if kwargs['latest_close'] < kwargs['ema_50'] else 'hold'}">
                        {'🟢 BUY: Price above both 50EMA and 200SMA' if kwargs['latest_close'] > kwargs['ema_50'] > kwargs['sma_200'] else 
                         '🔴 SELL: Price below 50EMA' if kwargs['latest_close'] < kwargs['ema_50'] else 
                         '🟡 HOLD: Mixed signals or ranging market'}
                    </p>
                    """}
                    """}
                </div>
            </div>
            
            <div class="chart">
                <img src="{kwargs['plot_url']}" alt="Stock Analysis Chart">
            </div>
        </div>
        """ if analysis_complete else ""}
    </div>
</body>
</html>"""
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
            
            return generate_html(
                ticker=ticker,
                analysis_complete=True,
                latest_close=latest_close,
                predicted_price=predicted_price,
                price_change=price_change,
                r2_score=r2_score,
                current_rsi=current_rsi,
                current_macd=current_macd,
                current_signal=current_signal,
                ema_50=ema_50,
                sma_200=sma_200,
                plot_url=plot_url
            )
    
    return generate_html()

if __name__ == "__main__":
    app.run(debug=True)
