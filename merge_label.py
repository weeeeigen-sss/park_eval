import pandas as pd
from pathlib import Path
import os

# 📁 マージしたいCSVファイルが入っているフォルダのパス
root = Path("/Users/Yusaku.Eigen/Desktop/20251007_車室監視_道玄坂２車室_1006_1013")

# 📄 見つかった eval.csv のパスを格納
csv_paths = []

# os.walkで再帰的に探索
for dirpath, _, filenames in os.walk(root):
    for filename in filenames:
        if filename == "label.csv":
            csv_paths.append(Path(dirpath) / filename)

if not csv_paths:
    print("⚠️ label.csv が見つかりませんでした。")
    exit()

print(f"✅ {len(csv_paths)} 件の label.csv を検出")

# すべてのCSVを読み込んで縦マージ
dfs = []
for p in csv_paths:
    try:
        df = pd.read_csv(p)
        df["source_folder"] = p.parent.name  # 元フォルダ名を追加（任意）
        dfs.append(df)
    except Exception as e:
        print(f"❌ 読み込み失敗: {p} ({e})")

merged_df = pd.concat(dfs, ignore_index=True)

# 出力先
out_path = root / "label.csv"

# Excel文字化け対策でUTF-8-SIG
merged_df.to_csv(out_path, index=False, encoding="utf-8-sig")

print(f"🎉 マージ完了: {out_path}")