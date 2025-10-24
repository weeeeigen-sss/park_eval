import shutil
from pathlib import Path

# ルートフォルダを指定
root = Path("/Users/Yusaku.Eigen/Desktop/20251021_車室監視_道玄坂２車室_1020_1026")

for target_name in ["IT", "META", "RAW"]:
    # target_name = "eval"  # まとめたいフォルダ名
    output_dir = root / "merged" / target_name
    output_dir.mkdir(parents=True, exist_ok=True)

    target_dir = root / "CAM1"

    # 再帰的に eval フォルダを探す
    for src in target_dir.rglob(target_name):
        if src.is_dir() and src.name == target_name:
            print(f"コピー中: {src}")
            # 各フォルダ内の全ファイルをコピー
            for file in src.glob("*"):
                if file.is_file():
                    # 同名ファイルがある場合、フォルダ名をprefixとして付加
                    dest = output_dir / f"{file.name}"

                    if file.resolve() != dest.resolve():
                        shutil.copy2(file, dest)
                    else:
                        print(file)
                    # shutil.copy2(file, dest)

print(f"完了: {output_dir}")