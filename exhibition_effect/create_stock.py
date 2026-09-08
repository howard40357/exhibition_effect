import yfinance as yf
import pandas as pd
import time
import sqlite3

tickers = {
    '廣達': '2382.TW', '華碩': '2357.TW', '威盛': '2388.TW', '迎廣': '6117.TW',
    '上銀': '2049.TW', '研華': '2395.TW', '所羅門': '2359.TW', '直得': '1597.TW'
}

data = {}

for name, code in tickers.items():
    print(f"正在下載 {name} ({code})...")
    stock = yf.Ticker(code)
    # 抓取歷史資料並只取 Adj Close
    df = stock.history(start='2024-01-01', end='2026-08-31')
    if not df.empty:
        data[name] = df['Close'] # yf.history 拿到的 Close 預設即為還原股價
    time.sleep(0.5) # 稍微小休息，避開 API 速率限制

# 合併成一個完整的 Dataframe
df_prices = pd.DataFrame(data)

print("\n--- 下載成功！資料前 5 筆 ---")
print(df_prices.head())

# 存成 CSV 備用
df_prices.to_csv('taiwan_stocks_2years.csv', encoding='utf-8-sig')
connection = sqlite3.connect("data/stock.db")
df_prices.to_sql("taiwan_stocks_2years",con=connection,if_exists="replace",index=True)
print("\n已成功儲存至 taiwan_stocks_2years.csv")

