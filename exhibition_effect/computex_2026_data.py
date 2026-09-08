import pandas as pd

# 1. 讀取兩年大盤股價總表
stocks_price = pd.read_csv("taiwan_stocks_2years.csv")
stocks_price["Date"] = pd.to_datetime(stocks_price["Date"]).dt.tz_localize(None)

# 2. 定義 Computex 專屬個股名單
company_cols = ["廣達", "華碩", "威盛", "迎廣"]
exhibition_name = "Computex電腦展"

print("⏳ 正在處理 2026 Computex 資料...")
computex_period_2026 = stocks_price[
    stocks_price["Date"].between("2026-04-03", "2026-06-12")
][["Date"] + company_cols].reset_index(drop=True)

all_results_26 = []
caar_results_26 = []
start_date_26 = "2026-06-02"  # 2026 實際開展日
start_dt_26 = pd.to_datetime(start_date_26)

t0_idx_26 = computex_period_2026[
    computex_period_2026["Date"] <= start_dt_26
].index[-1]

for company in company_cols:
  prices = computex_period_2026[company].values
  days = computex_period_2026["Date"].values
  n = len(prices)

  # 💡 直接利用 t0 索引減 20，精準定位 T-20 的價格
  target_k = t0_idx_26 - 20
  if 0 <= target_k < n:
    begin_price = prices[target_k]
  else:
    begin_price = prices[0]  # 防呆

  for k in range(n):
    rel_date = k - t0_idx_26  # 這就是你的相對日期

    if begin_price > 0:
      accumulative_ret = (prices[k] - begin_price) / begin_price * 100
    else:
      accumulative_ret = 0.0

    accumulative_ave_ret = (
        accumulative_ret / (k + 1) if (k + 1) > 0 else 0.0
    )

    caar_results_26.append({
        "Stock": company,
        "Date": days[k],
        "Relative_Date": rel_date,
        "Begin_price": begin_price,
        "Current_price": prices[k],
        "Accumulate_ret": round(accumulative_ret, 2),
        "Accumulate_ave_ret": round(accumulative_ave_ret, 2),
        "Exhibition": exhibition_name,
        "Year": 2026,
    })


  for i in range(n):
    buy_rel_date = i - t0_idx_26
    for j in range(i + 1, n):
      sell_rel_date = j - t0_idx_26
      p_in = prices[i]
      p_out = prices[j]
      ret = (p_out - p_in) / p_in * 100

      all_results_26.append({
          "Stock": company,
          "Buy_Index": i,
          "Sell_Index": j,
          "Relative_Date": buy_rel_date,
          "Sell_Relative_Date": sell_rel_date,
          "Buy_Date": days[i],
          "Sell_Date": days[j],
          "Holding_Days": j - i,
          "Return_%": round(ret, 2),
          "start_on": start_date_26,
          "Exhibition": exhibition_name,
          "Year": 2026,
      })

pd.DataFrame(all_results_26).to_csv(
    "computex_2026_return.csv", index=False, encoding="utf-8-sig"
)
pd.DataFrame(caar_results_26).to_csv(
    "computex_2026_accr.csv", index=False, encoding="utf-8-sig"
)

print(
    "✅ Computex 2026 的 computex_2026_return.csv 與 computex_2026_accr.csv"
    " 已成功產出！"
)