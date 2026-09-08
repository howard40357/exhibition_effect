import os
import runpy

# 自動切換工作目錄到 exhibition_effect 資料夾
target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exhibition_effect")
os.chdir(target_dir)

# 直接在當前環境執行 project_fix.py
runpy.run_path("project_fix.py", run_name="__main__")