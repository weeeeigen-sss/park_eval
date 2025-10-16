import pandas as pd
from pathlib import Path

# ルートフォルダ
root = Path("/Users/Yusaku.Eigen/Desktop/20251007_車室監視_道玄坂２車室_1006_1013/CAM1")  # ここを変更

# eval.csv を再帰的に取得
files = sorted(root.rglob("eval.csv"))

dfs = []
for f in files:
    col_name = f.parent.name
    df = pd.read_csv(f, header=None, index_col=0, names=["項目", col_name])
    dfs.append(df)

# 右に連結
merged = pd.concat(dfs, axis=1)

# 総和列と平均列を分けて計算
sum_items = ["検知総数", "車両総数", "入庫見逃し", "出庫見逃し", "誤出庫",
             "全桁OK", "全桁NG", "全桁NG（見切れ）", "全桁NG（影）",
             "全桁NG（FP）", "全桁NG（Blur）", "全桁NG（その他）",
             "GT不明", "再送回数"]

avg_items = ["全桁精度（メタごと）", "全桁精度（見切れ/FP抜き）"]

# 数値列のみ対象
numeric_cols = merged.select_dtypes(include="number")

# 総和列
merged["総和"] = merged.loc[sum_items].sum(axis=1)

# 平均列
merged["平均"] = merged.loc[avg_items].mean(axis=1)

# CSV出力
merged.to_csv(root / "eval_all.csv", encoding="utf-8-sig")

print(merged)