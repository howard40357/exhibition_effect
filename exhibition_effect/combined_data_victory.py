import pandas as pd

# 1. 讀取 4 個獨立建立好的買賣組合 CSV 檔案
df_2026_tairos = pd.read_csv('tairos_2026_return.csv')
df_2025_tairos = pd.read_csv('tairos_2025_return.csv')
df_2026_computex = pd.read_csv('computex_2026_return.csv')
df_2025_computex = pd.read_csv('computex_2025_return.csv')

# 2. 使用 pd.concat 上下垂直串接
df_all_trades = pd.concat(
    [df_2026_tairos, df_2025_tairos, df_2026_computex, df_2025_computex],
    ignore_index=True,
)

# 💡 關鍵清理 A：自動清除任何含有 "Unnamed" 的欄位
df_all_trades = df_all_trades.loc[
    :, ~df_all_trades.columns.str.contains('^Unnamed')
]

# 💡 關鍵清理 B：把不同名稱的開展日統一合併成一個 "start_on" 欄位
for col in ['Tairos_start_on', 'Computex_start_on']:
  if col in df_all_trades.columns:
    df_all_trades['start_on'] = df_all_trades['start_on'].fillna(
        df_all_trades[col]
    )
    df_all_trades = df_all_trades.drop(columns=[col])

# 3. 存成 combined_trades.csv
df_all_trades.to_csv('combined_trades.csv', index=False, encoding='utf-8-sig')

print(
    '✅ combined_trades.csv 合併完成！已自動對齊欄位、清除 Unnamed 並且統一'
    ' start_on 名稱。'
)