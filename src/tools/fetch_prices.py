import yfinance as yf
import json
import sys
import argparse

def fetch_prices(symbols):
    result = {}
    for symbol in symbols:
        try:
            # Ensure .NS suffix for Indian stocks if not present
            yf_symbol = symbol if symbol.endswith(".NS") or symbol.endswith(".BO") else f"{symbol}.NS"
            ticker = yf.Ticker(yf_symbol)
            
            # Use fast_info for max speed and accuracy
            try:
                price = ticker.fast_info['last_price']
            except:
                # Fallback
                info = ticker.info
                price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not price:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            if price:
                result[symbol] = float(price)
        except Exception as e:
            # Silently skip errors for individual symbols
            pass
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+", help="Symbols to fetch prices for")
    args = parser.parse_args()
    
    prices = fetch_prices(args.symbols)
    print(json.dumps(prices))
