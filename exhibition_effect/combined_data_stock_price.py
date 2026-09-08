import pandas as pd

# 1. 讀取 4 個獨立建立好的累積報酬 CSV 檔案
df_2026_tairos = pd.read_csv('tairos_2026_accr.csv')
df_2025_tairos = pd.read_csv('tairos_2025_accr.csv')
df_2026_computex = pd.read_csv('computex_2026_accr.csv')
df_2025_computex = pd.read_csv('computex_2025_accr.csv')

# 2. 賦予明確的 Exhibition 標籤與年份（如果原本子檔案還沒加的話）
df_2026_tairos['Exhibition'] = "Tairos機器人展"
df_2026_tairos['Year'] = 2026

df_2025_tairos['Exhibition'] = "Tairos機器人展"
df_2025_tairos['Year'] = 2025

df_2026_computex['Exhibition'] = "Computex電腦展"
df_2026_computex['Year'] = 2026

df_2025_computex['Exhibition'] = "Computex電腦展"
df_2025_computex['Year'] = 2025

# 3. 上下垂直串接
df_all_price = pd.concat(
    [df_2026_tairos, df_2025_tairos, df_2026_computex, df_2025_computex],
    ignore_index=True,
)

# 💡 關鍵清理：自動過濾掉任何含有 "Unnamed" 的欄位
df_all_price = df_all_price.loc[:, ~df_all_price.columns.str.contains('^Unnamed')]

# 4. 存成 combined_price.csv
df_all_price.to_csv('combined_price.csv', index=False, encoding='utf-8-sig')

print('✅ combined_price.csv 合併完成！已完美清除 Unnamed 欄位。')