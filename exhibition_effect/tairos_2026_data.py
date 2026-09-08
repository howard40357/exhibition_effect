import pandas as pd

stocks_price = pd.read_csv("taiwan_stocks_2years.csv")
stocks_price["Date"] = pd.to_datetime(stocks_price["Date"]).dt.tz_localize(None)

tairos_period_2026 = (
    stocks_price[stocks_price["Date"].between("2026-07-19", "2026-08-27")]
    .drop(labels=["廣達", "華碩", "威盛", "迎廣"], axis=1)
    .reset_index(drop=True)
)

company_cols = ["上銀", "研華", "所羅門", "直得"]
all_results = []
caar_results = []

start_date = "2026-08-19"
start_dt = pd.to_datetime(start_date)
exhibition_name = "Tairos機器人展"

t0_idx = tairos_period_2026[tairos_period_2026["Date"] <= start_dt].index[-1]

for company in company_cols:
  prices = tairos_period_2026[company].values
  days = tairos_period_2026["Date"].values
  n = len(prices)

  # 💡 利用 t0 索引減 20，精準鎖定 T-20 的價格作為基準價
  target_k = t0_idx - 20
  if 0 <= target_k < n:
    begin_price = prices[target_k]
  else:
    begin_price = prices[0]  # 防呆機制

  for k in range(n):
    rel_date = k - t0_idx

    if begin_price > 0:
      accumulative_ret = (prices[k] - begin_price) / begin_price * 100
    else:
      accumulative_ret = 0.0

    accumulative_ave_ret = (
        accumulative_ret / (k + 1) if (k + 1) > 0 else 0.0
    )

    caar_results.append({
        "Stock": company,
        "Date": days[k],
        "Relative_Date": rel_date,
        "Begin_price": begin_price,  # 這裡就會是 T-20 的價格
        "Current_price": prices[k],
        "Accumulate_ret": round(accumulative_ret, 2),
        "Accumulate_ave_ret": round(accumulative_ave_ret, 2),
        "Exhibition": exhibition_name,
        "Year": 2026,  # 順便補上 Year 欄位，確保資料一致
    })

  for i in range(n):
    buy_rel_date = i - t0_idx
    for j in range(i + 1, n):
      sell_rel_date = j - t0_idx
      p_in = prices[i]
      p_out = prices[j]
      ret = (p_out - p_in) / p_in * 100

      all_results.append({
          "Stock": company,
          "Buy_Index": i,
          "Sell_Index": j,
          "Relative_Date": buy_rel_date,
          "Sell_Relative_Date": sell_rel_date,
          "Buy_Date": days[i],
          "Sell_Date": days[j],
          "Holding_Days": j - i,
          "Return_%": round(ret, 2),
          "start_on": start_date,
          "Exhibition": exhibition_name,
          "Year": pd.to_datetime(days[i]).year
      })

pd.DataFrame(all_results).to_csv("tairos_2026_return.csv", encoding="utf-8-sig")
pd.DataFrame(caar_results).to_csv("tairos_2026_accr.csv", encoding="utf-8-sig")