import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# 1. 讀取專案中的 CSV 檔案
df_trades = pd.read_csv("combined_trades.csv")
df_trends = pd.read_csv("auto_fume_mix.csv")
df_prices = pd.read_csv("combined_price.csv")

# 資料清理與格式統一
for df in [df_trades, df_trends, df_prices]:
  if "Exhibition" in df.columns:
    df["Exhibition"] = (
        df["Exhibition"].astype(str).str.strip().str.replace(" ", "")
    )
  if "Stock" in df.columns:
    df["Stock"] = df["Stock"].astype(str).str.strip().str.replace(" ", "")
  if "Year" in df.columns:
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)

# 定義大型股清單
large_caps_map = {
    "Tairos機器人展": ["上銀", "研華"],
    "Computex電腦展": ["廣達", "華碩"],
}

exhibitions = df_trades["Exhibition"].dropna().unique()
years = sorted(df_trades["Year"].dropna().astype(int).unique())

output_filename = "exhibition_backtest_summary_3daysbefore.xlsx"
success_count = 0

with pd.ExcelWriter(output_filename, engine="openpyxl") as writer:
  for exh in exhibitions:
    exh_clean = exh.replace(" ", "")
    large_list = [s.replace(" ", "") for s in large_caps_map.get(exh_clean, [])]

    df_exh = df_trades[df_trades["Exhibition"] == exh]
    df_exh_trend = df_trends[df_trends["Exhibition"] == exh]

    all_stocks = sorted(df_exh["Stock"].dropna().unique().tolist())
    large_stocks = [s for s in large_list if s in all_stocks]
    small_stocks = [s for s in all_stocks if s not in large_list]

    row_labels = ["大型股平均", "小型股平均"] + all_stocks

    columns_data = []
    table_data = {label: [] for label in row_labels}

    # 針對每一個年份、過濾狀態、指標，當作一個欄位
    for yr in years:
      df_yr_trade = df_exh[df_exh["Year"] == yr]
      df_yr_trend = df_exh_trend[df_exh_trend["Year"] == yr]

      if df_yr_trade.empty:
        continue

      for filter_type in ["過濾前", "過濾後"]:
        for metric_name in ["勝率", "平均報酬"]:
          columns_data.append((str(yr), filter_type, metric_name))

          # 依序計算每一個 row（股票/平均）在該欄位的值
          for label in row_labels:
            if label == "大型股平均":
              target_s = large_stocks
            elif label == "小型股平均":
              target_s = small_stocks
            else:
              target_s = [label]

            if not target_s:
              table_data[label].append("N/A")
              continue

            if filter_type == "過濾前":
              df_sub = df_yr_trade[
                  (df_yr_trade["Stock"].isin(target_s))
                  & (df_yr_trade["Relative_Date"] >= -20)
                  & (df_yr_trade["Relative_Date"] <= -1)
              ]
            else:
              df_spike_days = (
                  df_yr_trend[
                      (df_yr_trend["Stock"].isin(target_s))
                      & (df_yr_trend["Relative_Date"] >= -20)
                      & (df_yr_trend["Relative_Date"] <= -1)
                  ]
                  .groupby("Relative_Date")["Daily_Spike"]
                  .mean()
                  .reset_index()
              )
              filtered_spike = df_spike_days[
                  df_spike_days["Daily_Spike"] >= 1.5
              ]

              if not filtered_spike.empty:
                first_spike_t = filtered_spike.iloc[0]["Relative_Date"]
                calc_start_t = first_spike_t - 3
                df_sub = df_yr_trade[
                    (df_yr_trade["Stock"].isin(target_s))
                    & (df_yr_trade["Relative_Date"] >= calc_start_t)
                    & (df_yr_trade["Relative_Date"] <= -1)
                ]
              else:
                df_sub = pd.DataFrame()

            if df_sub.empty:
              val = "無觸發" if filter_type == "過濾後" else 0.0
            else:
              if metric_name == "勝率":
                val = round((df_sub["Return_%"] > 0).mean() * 100, 2)
              else:
                val = round(df_sub["Return_%"].mean(), 2)

            table_data[label].append(val)

    if not columns_data:
      continue

    # 建立多層欄位 DataFrame（讓股票當欄位、年份過濾當列，或是反過來對齊你的截圖）
    multi_cols = pd.MultiIndex.from_tuples(columns_data)

    # 建立以 row_labels 為列、columns_data 為欄的 DataFrame
    df_result = pd.DataFrame(table_data, index=multi_cols).T
    df_result.to_excel(writer, sheet_name=exh[:30])
    success_count += 1

if success_count > 0:
  print(f"Excel 檔案已成功生成於專案資料夾內：{output_filename}")
else:
  print("警告：沒有成功寫入任何分頁，請檢查資料內容是否正確。")