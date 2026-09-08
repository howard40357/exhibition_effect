import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 一、 頁面配置與資料載入
# ==============================================================================
st.set_page_config(page_title="跨年份規律性與聲量過濾 A/B 測試", layout="wide")
st.title("專案：跨年份規律性與聲量過濾 A/B 測試 (Multi-Year Pattern & Volume Filter)")

st.sidebar.header("🎛️ 控制選單")


@st.cache_data
def load_data():
  base_dir = os.path.dirname(os.path.abspath(__file__))

  df_trades = pd.read_csv(os.path.join(base_dir, "combined_trades.csv"))
  df_trends = pd.read_csv(os.path.join(base_dir, "auto_fume_mix.csv"))
  df_prices = pd.read_csv(os.path.join(base_dir, "combined_price.csv"))

  # 強制清理字串空白與格式
  for df in [df_trades, df_trends, df_prices]:
    if "Exhibition" in df.columns:
      df["Exhibition"] = (
          df["Exhibition"].astype(str).str.strip().str.replace(" ", "")
      )
    if "Stock" in df.columns:
      df["Stock"] = df["Stock"].astype(str).str.strip().str.replace(" ", "")
    if "Year" in df.columns:
      df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)

  return df_trades, df_trends, df_prices


try:
  df_trades, df_trends, df_prices = load_data()
except Exception as e:
  st.error(f"資料載入失敗，請確認三個 CSV 檔案是否存在。詳細錯誤: {e}")
  st.stop()

# ==============================================================================
# 二、 側邊欄互動篩選
# ==============================================================================
exhibition_list = sorted(df_trades["Exhibition"].dropna().unique().tolist())
selected_exhibition = st.sidebar.selectbox("1️⃣ 選擇主題展覽", exhibition_list)

# 依展覽篩選年份
df_exh_trades = df_trades[df_trades["Exhibition"] == selected_exhibition]
available_years = sorted(
    df_exh_trades["Year"].dropna().astype(int).unique().tolist()
)
year_options = ["全部年份 (跨年對比)"] + [str(y) for y in available_years]
selected_year_str = st.sidebar.selectbox("2️⃣ 選擇檢視年份", year_options)

if selected_year_str == "全部年份 (跨年對比)":
  df_year_trades = df_exh_trades
  target_years = available_years
else:
  target_year = int(selected_year_str)
  df_year_trades = df_exh_trades[df_exh_trades["Year"] == target_year]
  target_years = [target_year]

# 定義大型股清單（同步去除空白）
exhibition_large_caps = {
    "Tairos機器人展": ["上銀", "研華"],
    "Computex電腦展": ["廣達", "華碩"],
}
# 容錯處理：把對應字典裡的名稱也去除空白
exhibition_large_caps_clean = {
    k.replace(" ", ""): [s.replace(" ", "") for s in v]
    for k, v in exhibition_large_caps.items()
}

current_exh_large = exhibition_large_caps_clean.get(
    selected_exhibition.replace(" ", ""), []
)
individual_stocks = sorted(df_year_trades["Stock"].dropna().unique().tolist())

stock_options = ["大型股平均", "小型股平均"] + individual_stocks
selected_target = st.sidebar.selectbox("3️⃣ 選擇檢視標的", stock_options)

enable_spike_filter = st.sidebar.toggle(
    "啟用 Google Trends 聲量濾網 (Spike Ratio >= 1.5)", value=True
)


# ==============================================================================
# 三、 A/B 測試核心邏輯
# ==============================================================================
def get_target_stocks(all_stocks):
  if selected_target == "大型股平均":
    return [s for s in current_exh_large if s in all_stocks]
  elif selected_target == "小型股平均":
    return [s for s in all_stocks if s not in current_exh_large]
  else:
    return [selected_target]


target_stocks = get_target_stocks(individual_stocks)

# 1. Group A (無濾網：T-20 ~ T-1 全期間)
df_group_a = df_year_trades[
    (df_year_trades["Stock"].isin(target_stocks))
    & (df_year_trades["Relative_Date"] >= -20)
    & (df_year_trades["Relative_Date"] <= -1)
].copy()

total_a = len(df_group_a)
win_rate_a = (
    (df_group_a["Return_%"] > 0).mean() * 100 if total_a > 0 else 0.0
)
avg_return_a = df_group_a["Return_%"].mean() if total_a > 0 else 0.0

# 2. Group B (聲量濾網：從 First Spike 當天一路到 T-1 的期間)
df_target_trends = df_trends[
    (df_trends["Exhibition"] == selected_exhibition)
    & (df_trends["Stock"].isin(target_stocks))
    & (df_trends["Relative_Date"] >= -20)
    & (df_trends["Relative_Date"] <= -1)
]

if selected_year_str != "全部年份 (跨年對比)":
  df_target_trends = df_target_trends[
      df_target_trends["Year"] == int(selected_year_str)
  ]

df_spike_days = (
    df_target_trends.groupby("Relative_Date")["Daily_Spike"]
    .mean()
    .reset_index()
)
df_spike_filtered = df_spike_days[df_spike_days["Daily_Spike"] >= 1.5].sort_values(
    "Relative_Date"
)

if not df_spike_filtered.empty:
  first_spike_t = df_spike_filtered.iloc[0]["Relative_Date"]

  # 💡 修正：Group B 改為抓取從 First Spike 觸發日至 T-1 的完整區間
  df_group_b = df_year_trades[
      (df_year_trades["Stock"].isin(target_stocks))
      & (df_year_trades["Relative_Date"] >= first_spike_t)
      & (df_year_trades["Relative_Date"] <= -1)
  ].copy()

  total_b = len(df_group_b)
  win_rate_b = (
      (df_group_b["Return_%"] > 0).mean() * 100 if total_b > 0 else 0.0
  )
  avg_return_b = df_group_b["Return_%"].mean() if total_b > 0 else 0.0
  first_spike_label = f"T{int(first_spike_t):+d} ~ T-1"
else:
  win_rate_b, avg_return_b = 0.0, 0.0
  first_spike_label = "展前無觸發 Spike"

display_win_rate = win_rate_b if enable_spike_filter else win_rate_a
display_avg_return = avg_return_b if enable_spike_filter else avg_return_a

# ==============================================================================
# 四 / 五、 KPI 與折線圖
# ==============================================================================
st.subheader(
    f"📊 A/B 測試績效比較 — [{selected_exhibition} | {selected_year_str} |"
    f" {selected_target}]"
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Group A 原始勝率 (T-20 ~ T-1)", f"{win_rate_a:.1f}%")
col2.metric(
    f"Group B 濾網後勝率 ({first_spike_label if enable_spike_filter else '未啟用'})",
    f"{display_win_rate:.1f}%",
    delta=(
        f"{display_win_rate - win_rate_a:+.1f}%"
        if enable_spike_filter
        else "未啟用"
    ),
)
col3.metric("Group A 原始平均報酬率", f"{avg_return_a:.2f}%")
col4.metric(
    "Group B 濾網後平均報酬率",
    f"{display_avg_return:.2f}%",
    delta=(
        f"{display_avg_return - avg_return_a:+.2f}%"
        if enable_spike_filter
        else "未啟用"
    ),
)

st.divider()

st.subheader(
    f"📈 累積報酬率軌跡 (Relative Trading Days) — [{selected_target}]"
)
fig = go.Figure()

df_price_target_raw = df_prices[
    (df_prices["Exhibition"] == selected_exhibition)
    & (df_prices["Stock"].isin(target_stocks))
    & (df_prices["Relative_Date"] >= -20)
    & (df_prices["Relative_Date"] <= 5)
]

if selected_target in ["大型股平均", "小型股平均"]:
  df_price_target = (
      df_price_target_raw.groupby(["Year", "Relative_Date"])["Accumulate_ret"]
      .mean()
      .reset_index()
  )
else:
  df_price_target = df_price_target_raw

colors = ["#636EFA", "#EF553B", "#FFA15A", "#19D3F3", "#AB63FA"]

if selected_year_str == "全部年份 (跨年對比)":
  years_found = sorted(df_price_target["Year"].dropna().unique())
  cum_list = []
  for idx, yr in enumerate(years_found):
    df_yr = df_price_target[df_price_target["Year"] == yr]
    if not df_yr.empty:
      cum_list.append(df_yr.set_index("Relative_Date")["Accumulate_ret"])
      fig.add_trace(
          go.Scatter(
              x=df_yr["Relative_Date"],
              y=df_yr["Accumulate_ret"],
              mode="lines+markers",
              name=f"{selected_target} ({int(yr)})",
              line=dict(color=colors[idx % len(colors)]),
          )
      )
  if cum_list:
    df_combined_cum = pd.concat(cum_list, axis=1).mean(axis=1).reset_index()
    df_combined_cum.columns = ["Relative_Date", "Mean_Ret"]
    fig.add_trace(
        go.Scatter(
            x=df_combined_cum["Relative_Date"],
            y=df_combined_cum["Mean_Ret"],
            mode="lines",
            name="Multi-Year Baseline (多年平均)",
            line=dict(color="#00CC96", width=4),
        )
    )
else:
  target_yr = int(selected_year_str)
  df_yr = df_price_target[df_price_target["Year"] == target_yr]
  if not df_yr.empty:
    fig.add_trace(
        go.Scatter(
            x=df_yr["Relative_Date"],
            y=df_yr["Accumulate_ret"],
            mode="lines+markers",
            name=f"{selected_target} ({target_yr})",
            line=dict(color="#EF553B", width=3),
        )
    )

  df_all_exh_yr = df_prices[
      (df_prices["Exhibition"] == selected_exhibition)
      & (df_prices["Year"] == target_yr)
      & (df_prices["Relative_Date"] >= -20)
      & (df_prices["Relative_Date"] <= 5)
  ]
  if not df_all_exh_yr.empty:
    df_baseline = (
        df_all_exh_yr.groupby("Relative_Date")["Accumulate_ret"]
        .mean()
        .reset_index()
    )
    fig.add_trace(
        go.Scatter(
            x=df_baseline["Relative_Date"],
            y=df_baseline["Accumulate_ret"],
            mode="lines",
            name=f"{selected_exhibition} {target_yr} 全體概念股平均 Baseline",
            line=dict(color="#00CC96", width=3, dash="dash"),
        )
    )

if enable_spike_filter and not df_spike_filtered.empty:
  fig.add_vline(
      x=first_spike_t,
      line_width=2,
      line_dash="dot",
      line_color="#FFA15A",
      annotation_text=f"First Spike (T{int(first_spike_t):+d})",
  )

fig.add_vline(
    x=0,
    line_width=2,
    line_dash="solid",
    line_color="gray",
    annotation_text="開展日 (T=0)",
)

fig.update_layout(
    title=f"{selected_exhibition} | {selected_target} | {selected_year_str}",
    xaxis_title="相對交易日 (Relative Trading Day)",
    yaxis_title="累積報酬率 (%) (以 T-20 為 0%)",
    hovermode="x unified",
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)