# 2車室データ集計ツール

`main.py` で起動する、2車室データのラベリング・集計（評価）用GUIツールです。

## 1. セットアップ

### 前提

- Python 3.11 以上
- macOS / Windows（PyQt6が動作する環境）

### 依存パッケージのインストール

`uv` を使う場合（推奨）:

```bash
uv sync
```

`r.txt` を使う場合（uv pip）:

```bash
uv pip install -r r.txt
```

`pyproject.toml` を使う場合:

```bash
pip install -e .
```

`r.txt` を使う場合:

```bash
pip install -r r.txt
```

## 2. 入力データ構成

読み込み対象フォルダは、基本的に以下の構成を想定しています。

```text
<data_dir>/
	META/            # メタJSON
	IT/              # プレート/車両画像
	RAW/             # 生画像
	label.csv        # 既存ラベル（任意）
	param.json       # 読み込み期間制限（任意）
```

### JSON配置について

- 標準: `META/*.json`
- ebsim形式: `t4meta/*.json` も読み込み可能

### 任意ファイル

- `label.csv`: 既存ラベルがあれば起動時に反映
- `param.json`: 読み込み対象の開始/終了時刻を制限
	- `start`, `end`, `format` を使って期間指定
- `roi.json`（ebsim用）: ROIを使って対象データを選択

## 3. 起動方法

### 通常起動（GUIでフォルダ選択）

```bash
python main.py
```

### データフォルダを指定して起動

```bash
python main.py /path/to/data_dir
```

例:

```bash
python main.py sample_data/20250910
```

## 4. 画面の使い方

画面は大きく `labeling` タブと `eval` タブで構成されます。

### labelingタブ

- 時系列に3フレーム表示（中央が現在注目インデックス）
- 画像・LP・ステータス・各種フラグを確認/編集
- 主要な編集項目:
	- ステータス（OK / NG種別 / 誤出庫 / Moving入出庫）
	- 初回
	- GT不明
	- 入庫見逃し
	- 出庫見逃し
	- 誤入庫（FP）
	- 誤入庫（隣接）

### ツールバー機能

- `Load`: データフォルダ読込
- `Lot` プルダウン: 車室単位で絞り込み（`All`含む）
- `Moving` / `Stop` / `None`: `Vehicle_Status` で表示対象を絞り込み
- `Save`: `label.csv` / `eval.csv` を保存
- `AutoLabel Moving`: Moving系の自動ラベル付け
- `Eval Movement`: MovingOut評価補助処理
- `Show Status` / `Show Plate` / `Show Vehicle`: RAW画像上の表示切替

### フィルタパネル

2段フィルタで対象を素早く確認できます。

- 1段目: ステータス（None / OK / 各NG / 誤出庫 ...）
- 2段目: オプション条件
	- GT不明
	- 入庫見逃し / 出庫見逃し
	- 誤入庫（FP）/ 誤入庫（隣接）
	- 初回=True / 初回=False
	- PlateConf=NG/OK
	- TopFormat=NG/OK
	- BottomFormat=NG/OK
	- MoveY=NG/OK

### evalタブ

集計結果を表形式で表示します。

- 検知総数 / 車両総数
- 入庫見逃し / 出庫見逃し
- 誤入庫（FP / 隣接）
- 誤出庫
- 全桁OK / 各種NG内訳
- GT不明 / 再送回数
- 精度指標（メタごと、車両ごと等）

## 5. キーボードショートカット

### ナビゲーション

- `←` / `→`: 前後フレームへ移動
- `↑` / `↓`: フィルタ一致データを前後移動

### ステータス割り当て

- `1`: OK
- `2`: NG（見切れ）
- `3`: NG（影）
- `4`: NG（Occlusion）
- `5`: NG（FP）
- `6`: NG（ブラー）
- `7`: NG（白飛び）
- `8`: NG（AIモデル）
- `9`: NG（その他）
- `0`: 誤出庫
- `F`: 初回フラグ ON/OFF

### 補助

- `Ctrl+C`: ウィンドウ全体のスクリーンショットをクリップボードへコピー
- `Ctrl+Shift+[` / `Ctrl+Shift+]`: タブ切替

## 6. 出力ファイル

`Save` 実行時、読み込み元フォルダに以下を出力します。

- `label.csv`: ラベリング結果
- `eval.csv`: 集計結果

## 7. 補足

- `is_first` は `Vehicle_Status == Stop` または `誤出庫` 時に操作対象
- 画像ファイルが欠けていると表示が崩れるため、`IT` / `RAW` の欠損に注意