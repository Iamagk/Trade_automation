import yfinance as yf
import json
import sys
import argparse

def fetch_prices(symbols):
    result = {}
    for original_symbol in symbols:
        try:
            # Ensure .NS suffix for Indian stocks 
            yf_symbol = original_symbol
            if not (original_symbol.endswith(".NS") or original_symbol.endswith(".BO")):
                yf_symbol = f"{original_symbol}.NS"
                
            ticker = yf.Ticker(yf_symbol)
            
            price = None
            # Try fast_info
            try:
                price = ticker.fast_info['last_price']
            except:
                pass
            
            # Fallback 1: info
            if not price:
                try:
                    info = ticker.info
                    price = info.get('currentPrice') or info.get('regularMarketPrice')
                except:
                    pass
            
            # Fallback 2: history
            if not price:
                try:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                except:
                    pass
            
            if price:
                # Map back to the ORIGINAL symbol passed by Node.js
                result[original_symbol] = float(price)
        except Exception:
            pass
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+", help="Symbols to fetch prices for")
    args = parser.parse_args()
    
    prices = fetch_prices(args.symbols)
    print(json.dumps(prices))
