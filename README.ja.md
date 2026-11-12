# REA-Video-Pro-Max

## 編集の仕組みを読み解き、そのスタイルで新しい動画を。

**参考動画から根拠付きのタイムラインと再利用可能なスタイルテンプレートを作成。別の台本とメディアを組み合わせ、自分の動画をレンダリングします。**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[記録済みデモ](docs/index.html) · [動画 A](docs/media/reference.mp4) · [動画 B](docs/media/adapted.mp4) · [検証記録 (English)](docs/VALIDATION.md)

良い編集には、カットの位置、字幕のまとまり、強調する単語、動きの収まり、音との同期といった判断があります。REA-Video-Pro-Maxは、対応範囲内の判断を確認し、再利用できる形にします。

```text
動画 A → 分析＋推論タイムライン → スタイルテンプレート＋新しい内容 → 編集可能なプロジェクト → 動画 B
```

デモはプロジェクトが所有する合成メディアを使用します。AとBでは文字とメディアが異なります。静的サイトは記録済みの結果を表示し、ライブ推論や閲覧者の動画アップロードを行いません。

## できる依頼

- 動画全体をショット、字幕スタイル、動き、音のキュー、タイムラインに分解し、時刻付きの根拠を残します。
- 単一フレームのタイポグラフィ、レイアウト、色を分析します。一枚の画像から動きの時間や音は確定できません。
- 抽出したスタイルに新しい台本、画像、映像素材を適用して別の動画を作ります。
- 分析だけの依頼では、タイムラインと分析ファイルだけで完了できます。

```text
REA-Video-Pro-Maxでreference.mp4のタイムラインとスタイルを分析してください。新しい台本と私の素材を使い、字幕、動き、編集リズムが似た別の動画を作成してください。テンプレート、プロジェクト、動画と未検証の点を渡してください。
```

## 最初の結果まで

Python 3.11+、FFmpeg、FFprobeが必要です。Python側はPillow、NumPy、PyAVを使用します。OCR用のTesseractは任意で、実行可能な言語はインストール済み言語データによって決まります。[対応表 (English)](docs/SUPPORT-MATRIX.md)で検証範囲を確認してください。

macOSが実測済みの開発環境です。LinuxはCIの予定対象で、Windowsのネイティブレンダラーは認証されていません。生成検証は正確なレンダー記録のハッシュと独立したOCR検査を必要とするため、一連のデモにはTesseractと`eng`データが必要です。

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

コマンドはGitチェックアウト構成を前提としています。配布スキルの展開先では`scripts/rea-video-pro-max.py`を使い、`lib`、`assets`、`references`も一緒に保持します。依存関係を入れたPythonを使用し、入口スクリプトだけをコピーしないでください。

## 自分の内容を入力

`examples/content.json`はcontent bindingの合成例です。新しい各シーンに`id`、`text`、`duration`、`background`、`accent`、任意の`asset`パスを指定します。`width`、`height`、`fps`は出力設定で、`audio`と`font`も任意です。メディアパスはbindingファイルの場所を基準に解決します。プロジェクトは素材とハッシュを記録し、Aの映像や音楽を無断で代用しません。新しい発話には新しい時間情報を作り、正確なアラインメントがない場合は推定方法を明示します。

シーン映像の音声はミュートされます。音は新しい`audio`バインディングで別途指定してください。短い映像は最終フレームを保持し、ネイティブ入力映像は正しい向きの正方形ピクセルである必要があります。CSVはショット行のみです。複雑な文字や双方向文字は組版・グループ分けの対応範囲を先に確認してください。

## Claude Code / Codexで使う

`skills/rea-video-pro-max`フォルダ全体をホストのスキルディレクトリにコピーするか、エージェントにチェックアウトからのインストールを依頼します。プロジェクト内では通常`.claude/skills/rea-video-pro-max`または`.agents/skills/rea-video-pro-max`です。スキルを入れてもFFmpeg、OCR言語データ、モデル重みは入りません。ホストのアカウント、実行権限、データポリシーは別です。[スキル](skills/rea-video-pro-max/SKILL.md)と技術資料はEnglishです。

## データとエクスポート

- Native JSONは分析、タイムライン、字幕・スタイル・モーション・音、テンプレートとプロジェクトを保持します。CSVは編集データの確認に使います。
- SRT/WebVTT/ASSは各形式の対応範囲で文字と時間情報を出力します。SRTは完全な書式や動きを保持しません。
- インストール版がavailableと報告したタイムラインアダプタを使います。receiptは対応部分、近似、損失を示し、すべての編集ソフトで効果を再現する保証ではありません。
- ソフトウェアレンダラーは新しい内容を組み立て、FFmpegで動画化します。FFmpegの任意フィルタ`drawtext`、`ass`、`subtitles`は不要です。

## 重要な制限

測定メタデータ、OCR検出、スタイルの推定、制作方法の仮説は別々の根拠です。書き出された動画だけから、元素材、隠れたレイヤー、元のフォント・プラグイン・編集プロジェクト、AIプロンプトを一意に復元することはできません。初期範囲は時間、字幕と対応する2D要素です。万能な動画デコンパイラや、市場最強と実証された製品ではありません。複雑な遮蔽、3D、HDRマスタリング、任意NLE往復は検証範囲外です。複雑な文字の整形には別途サポートとテストが必要で、README翻訳数はOCR・描画言語の認定数ではありません。

動画Bは新しい内容、スタイル契約、再生状態で検証します。Aとの全画面ピクセル一致で採点しません。技術確認と人間による創作評価は区別します。[検証と制限 (English)](docs/VALIDATION.md)。

## ローカル処理とクレジット

コア処理はローカルで実行し、有料API、ホスト型推論への動画アップロード、自動公開を必要としません。依存関係のインストールや任意providerでは通信が発生する場合があります。Claude/Codexホストのポリシーは別です。[Privacy (English)](docs/PRIVACY.md)。JuneYaooo/rea-videoに着想を得た独立製品であり、公式アップグレードではありません。ソース、フォント、メディア、コーデック、モデルの条件はそれぞれ適用されます。

ローカルレポートは既定で参考メディアと根拠ファイルをコピーします。`report --no-media`は完全なメディアコピーだけを省き、OCRテキスト、ローカルパス、切り抜きは残ります。共有前に確認してください。

[サポート (English)](SUPPORT.md) · [保守 (English)](docs/MAINTENANCE.md) · 専門のネイティブ翻訳者による査読済みとは主張していません。

[ローカル音声と高度なモーション（英語技術資料）](skills/rea-video-pro-max/references/speech-and-motion.md).
