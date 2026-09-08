from pytrends.request import TrendReq
import pandas as pd

# 1. 讀取大盤股價總表（用來取得正確的台股交易日與 t0_idx）
stocks_price = pd.read_csv("taiwan_stocks_2years.csv")
stocks_price["Date"] = pd.to_datetime(stocks_price["Date"]).dt.tz_localize(None)


def fetch_and_process_google_trends_trading_days(
    keywords, exhibition, year, start_date, end_date, start_on, stocks_df
):
  print(f"正在抓取並對齊 {year} {exhibition} 關鍵字: {keywords} ...")

  # 2. 抓取 Google Trends 原始日資料
  pytrends = TrendReq(hl="zh-TW", tz=-480)
  timeframe = f"{start_date} {end_date}"
  pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo="TW")

  df_trends = pytrends.interest_over_time()

  if df_trends.empty:
    raise ValueError(
        f"未抓取到 {exhibition} ({year}) 的 Google Trends 資料，請檢查日期範圍！"
    )

  if "isPartial" in df_trends.columns:
    df_trends = df_trends.drop(columns=["isPartial"])

  df_trends = df_trends.reset_index()
  df_trends["Date"] = pd.to_datetime(df_trends["date"])

  # 3. 篩選出該任務對應區間的台股真實交易日
  mask = (stocks_df["Date"] >= start_date) & (stocks_df["Date"] <= end_date)
  trading_days_df = stocks_df.loc[
      mask, ["Date"]
  ].drop_duplicates().sort_values("Date").reset_index(drop=True)

  if trading_days_df.empty:
    raise ValueError(f"在範圍 {start_date} 至 {end_date} 內找不到對應的台股交易日！")

  # 4. 計算該展覽的開展日 (t0) 在交易日陣列中的索引位置 (t0_idx)
  start_dt = pd.to_datetime(start_on)
  valid_t0 = trading_days_df[trading_days_df["Date"] <= start_dt]
  if valid_t0.empty:
    raise ValueError(f"開展日 {start_on} 小於所選交易日區間的起點！")
  t0_idx = valid_t0.index[-1]

  # 5. 將 Google Trends 的日曆日對齊到台股交易日
  # 原理：將週末/假日的聲量對齊到「下一個開盤的交易日」（或依需求調整），並計算平均
  # 先建立一個日曆日對應到下一個交易日的對照邏輯
  trading_days_list = trading_days_df["Date"].tolist()


  # 定義一個對齊函數：把任意日期對應到台股交易日
  def map_to_trading_day(d):
    # 如果剛好是交易日，就是自己
    if d in trading_days_list:
      return d
    # 如果是非交易日（如週末），找下一個最近的交易日
    future_days = [td for td in trading_days_list if td > d]
    return future_days[0] if future_days else None


  df_trends["Trading_Date"] = df_trends["Date"].apply(map_to_trading_day)
  df_trends = df_trends.dropna(subset=["Trading_Date"])

  # 若週末跟周一對應到同一天，取平均或合併聲量
  df_trends_aligned = (
      df_trends.groupby("Trading_Date")[keywords].mean().reset_index()
  )
  df_trends_aligned = df_trends_aligned.rename(
      columns={"Trading_Date": "Date"}
  )

  # 6. 建立長表格並計算「交易日序數差」(Relative_Date)
  long_rows = []
  n_trading_days = len(trading_days_df)

  for k in range(n_trading_days):
    curr_date = trading_days_df.loc[k, "Date"]
    rel_date = k - t0_idx  # 完美的交易日距離差（與股價檔同步！）

    # 找出該交易日對應的 SVI 數值
    match_row = df_trends_aligned[df_trends_aligned["Date"] == curr_date]

    for kw in keywords:
      if not match_row.empty:
        svi_val = match_row[kw].values[0]
      else:
        svi_val = 0  # 缺值防護

      long_rows.append({
          "Date": curr_date,
          "Stock": kw,
          "SVI": round(svi_val,2),
          "Exhibition": exhibition,
          "Year": year,
          "start_on": start_on,
          "Relative_Date": rel_date,
      })

  temp_df = pd.DataFrame(long_rows)

  # 7. 計算 MA20 與 Daily_Spike（基於交易日序列滾動）
  final_rows = []
  for kw in keywords:
    kw_df = temp_df[temp_df["Stock"] == kw].sort_values("Date").copy()
    kw_df["MA20"] = round(
        kw_df["SVI"].rolling(window=20, min_periods=1).mean(), 2
    )
    kw_df["Daily_Spike"] = round(kw_df["SVI"] / (kw_df["MA20"] + 0.1), 2)
    final_rows.append(kw_df)

  return pd.concat(final_rows, ignore_index=True)


# ==============================================================================
# 任務設定
# ==============================================================================
tasks = [
    {
        "exhibition": "Tairos機器人展",
        "year": 2026,
        "keywords": ["上銀", "研華", "所羅門", "直得"],
        "start": "2026-07-19",
        "end": "2026-08-27",
        "start_on": "2026-08-19",
    },
    {
        "exhibition": "Tairos機器人展",
        "year": 2025,
        "keywords": ["上銀", "研華", "所羅門", "直得"],
        "start": "2025-07-20",
        "end": "2025-08-28",
        "start_on": "2025-08-20",
    },
    {
        "exhibition": "Computex電腦展",
        "year": 2026,
        "keywords": ["廣達", "華碩", "威盛", "迎廣"],
        "start": "2026-05-02",
        "end": "2026-06-10",
        "start_on": "2026-06-02",
    },
    {
        "exhibition": "Computex電腦展",
        "year": 2025,
        "keywords": ["廣達", "華碩", "威盛", "迎廣"],
        "start": "2025-04-20",
        "end": "2025-05-28",
        "start_on": "2025-05-20",
    },
]

all_dfs = []

for task in tasks:
  df_task = fetch_and_process_google_trends_trading_days(
      task["keywords"],
      task["exhibition"],
      task["year"],
      task["start"],
      task["end"],
      task["start_on"],
      stocks_price,
  )
  all_dfs.append(df_task)

df_final = pd.concat(all_dfs, ignore_index=True)
df_final.to_csv("auto_fume_mix.csv", index=False, encoding="utf-8-sig")

print(
    "🎉 auto_fume_mix.csv 已成功改用【交易日序數】對齊，"
    "Relative_Date 將與股價表完美同步！"
)