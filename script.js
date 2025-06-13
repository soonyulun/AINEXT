// Stock Analysis Logic
document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.addEventListener('click', analyzeStock);
});

async function analyzeStock() {
    const ticker = document.getElementById('tickerInput').value.toUpperCase();
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        // Fetch stock data
        const stockData = await fetchStockData(ticker);

        // Calculate indicators
        const indicators = calculateIndicators(stockData);

        // Make prediction (simplified linear regression)
        const prediction = simpleLinearPrediction(stockData.close);

        // Display results
        displayResults(ticker, stockData, indicators, prediction);

        // Create charts
        createCharts(stockData, indicators);

        loading.classList.add('hidden');
        results.classList.remove('hidden');
    } catch (error) {
        loading.classList.add('hidden');
        alert(`Error: ${error.message}`);
    }
}

async function fetchStockData(ticker) {
    try {
        // Using Yahoo Finance API via RapidAPI (you'll need an API key)
        const response = await axios.get(
            `https://yahoo-finance15.p.rapidapi.com/api/yahoo/hi/history/${ticker}/1d`,
            {
                headers: {
                    'X-RapidAPI-Key': 'your-api-key',
                    'X-RapidAPI-Host': 'yahoo-finance15.p.rapidapi.com'
                },
                params: {
                    diffandsplits: 'false'
                }
            }
        );

        // Alternative free API if Yahoo doesn't work:
        // const response = await axios.get(`https://financialmodelingprep.com/api/v3/historical-price-full/${ticker}?apikey=YOUR_API_KEY`);

        const data = response.data;
        const dates = data.items.map(item => new Date(item.date * 1000));
        const closes = data.items.map(item => item.close);

        return {
            dates: dates,
            close: closes,
            high: data.items.map(item => item.high),
            low: data.items.map(item => item.low),
            volume: data.items.map(item => item.volume)
        };
    } catch (error) {
        throw new Error('Failed to fetch stock data');
    }
}

function calculateIndicators(data) {
    // Calculate RSI
    const rsi = calculateRSI(data.close);

    // Calculate MACD
    const { macd, signal } = calculateMACD(data.close);

    // Calculate moving averages
    const ema50 = calculateEMA(data.close, 50);
    const sma200 = calculateSMA(data.close, 200);

    return {
        rsi: rsi,
        macd: macd,
        signal: signal,
        ema50: ema50,
        sma200: sma200
    };
}

function calculateRSI(prices, period = 14) {
    let gains = [];
    let losses = [];

    for (let i = 1; i < prices.length; i++) {
        const change = prices[i] - prices[i-1];
        gains.push(change > 0 ? change : 0);
        losses.push(change < 0 ? Math.abs(change) : 0);
    }

    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

    let rsiValues = [];

    for (let i = period; i < prices.length; i++) {
        avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
        avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;

        const rs = avgGain / avgLoss;
        rsiValues.push(100 - (100 / (1 + rs)));
    }

    // Pad beginning with null values for alignment
    return Array(period).fill(null).concat(rsiValues);
}

function calculateEMA(prices, period) {
    const multiplier = 2 / (period + 1);
    let ema = [prices[0]]; // Start with first price

    for (let i = 1; i < prices.length; i++) {
        ema.push((prices[i] - ema[i-1]) * multiplier + ema[i-1]);
    }

    return ema;
}

function calculateSMA(prices, period) {
    return prices.map((_, index) => {
        if (index < period - 1) return null;
        const sum = prices.slice(index - period + 1, index + 1).reduce((a, b) => a + b, 0);
        return sum / period;
    });
}

function calculateMACD(prices) {
    const ema12 = calculateEMA(prices, 12);
    const ema26 = calculateEMA(prices, 26);
    const macd = ema12.map((val, i) => val - ema26[i]);
    const signal = calculateEMA(macd.filter(val => val !== null), 9);

    // Pad signal line for alignment
    const paddedSignal = Array(macd.length - signal.length).fill(null).concat(signal);

    return {
        macd: macd,
        signal: paddedSignal
    };
}

function simpleLinearPrediction(prices, days = 10) {
    // Simple linear regression for last 30 days
    const recentPrices = prices.slice(-30);
    const x = recentPrices.map((_, i) => i);
    const y = recentPrices;

    const n = x.length;
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.map((val, i) => val * y[i]).reduce((a, b) => a + b, 0);
    const sumXX = x.map(val => val * val).reduce((a, b) => a + b, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Predict next 'days' values
    const lastX = x[x.length - 1];
    const prediction = intercept + slope * (lastX + days);

    return {
        price: prediction,
        changePercent: ((prediction - y[y.length - 1]) / y[y.length - 1] * 100))  // Fixed: Added missing )
    };
}

function displayResults(ticker, stockData, indicators, prediction) {
    const latestClose = stockData.close[stockData.close.length - 1];
    const latestRsi = indicators.rsi[indicators.rsi.length - 1];
    const latestMacd = indicators.macd[indicators.macd.length - 1];
    const latestSignal = indicators.signal[indicators.signal.length - 1];
    const ema50 = indicators.ema50[indicators.ema50.length - 1];
    const sma200 = indicators.sma200[indicators.sma200.length - 1];

    // Update DOM elements
    document.getElementById('stockTitle').textContent = `${ticker} Analysis`;
    document.getElementById('currentPrice').textContent = `Current: $${latestClose.toFixed(2)}`;
    document.getElementById('prediction').textContent =
        `Predicted (10 days): $${prediction.price.toFixed(2)} (${prediction.changePercent.toFixed(1)}%)`;

    document.getElementById('rsiValue').textContent = `${latestRsi ? latestRsi.toFixed(1) : 'N/A'}`;
    document.getElementById('macdValue').textContent =
        `${latestMacd ? latestMacd.toFixed(2) : 'N/A'} ${latestMacd > latestSignal ? '↑' : '↓'}`;

    const trendText = latestClose > ema50 && ema50 > sma200 ? 'Bullish' : 'Bearish';
    document.getElementById('trendValue').textContent = trendText;

    // Generate recommendation
    let recommendation = '';
    if (prediction.changePercent > 5) {
        recommendation = '🟢 STRONG BUY: Expected significant price increase';
    } else if (prediction.changePercent > 2) {
        recommendation = '🟢 BUY: Expected moderate price increase';
    } else if (prediction.changePercent < -5) {
        recommendation = '🔴 STRONG SELL: Expected significant price decrease';
    } else if (prediction.changePercent < -2) {
        recommendation = '🔴 SELL: Expected moderate price decrease';
    } else {
        recommendation = '🟡 HOLD: Expected minimal price movement';
    }

    document.getElementById('recommendationText').textContent = recommendation;
}

function createCharts(stockData, indicators) {
    const dates = stockData.dates.slice(-200); // Last 200 days

    // Price Chart with Moving Averages
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: dates.map(date => date.toLocaleDateString()),
            datasets: [
                {
                    label: 'Price',
                    data: stockData.close.slice(-200),
                    borderColor: 'blue',
                    tension: 0.1
                },
                {
                    label: '50-EMA',
                    data: indicators.ema50.slice(-200),
                    borderColor: 'orange',
                    tension: 0.1
                },
                {
                    label: '200-SMA',
                    data: indicators.sma200.slice(-200),
                    borderColor: 'red',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Price and Moving Averages'
                }
            }
        }
    });

    // RSI Chart
    const rsiCtx = document.getElementById('rsiChart').getContext('2d');
    new Chart(rsiCtx, {
        type: 'line',
        data: {
            labels: dates.map(date => date.toLocaleDateString()),
            datasets: [{
                label: 'RSI(14)',
                data: indicators.rsi.slice(-200),
                borderColor: 'purple',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Relative Strength Index (RSI)'
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 10
                    }
                }
            }
        }
    });

    // MACD Chart
    const macdCtx = document.getElementById('macdChart').getContext('2d');
    new Chart(macdCtx, {
        type: 'line',
        data: {
            labels: dates.map(date => date.toLocaleDateString()),
            datasets: [
                {
                    label: 'MACD',
                    data: indicators.macd.slice(-200),
                    borderColor: 'blue',
                    tension: 0.1
                },
                {
                    label: 'Signal',
                    data: indicators.signal.slice(-200),
                    borderColor: 'red',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'MACD (Moving Average Convergence Divergence)'
                }
            }
        }
    });
}
