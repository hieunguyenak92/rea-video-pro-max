# REA-Video-Pro-Max

## ClaudeとCodexに、編集者の眼を。

**参考動画のテンポ、字幕、動きを読み解く。その編集判断を再利用できるスタイルに変え、自分の言葉と素材で新しい動画をレンダリング。**

優れた編集には、独自の言語があります。その表現を、あなたの創作道具に。

[**▶ ライブデモを見る**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**スキルを入手**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [リリース v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Claude Code / Codexスキル · CLI + 任意のMCP · ローカル処理 · Apache-2.0**

---

## 「この編集、好きだ」から「これが自分の作品」へ。

カットのリズム、字幕が入る瞬間、フレーズごとに変わる強調色、静止画に勢いを与えるズーム。惹きつけられる動画には、そんな選択が詰まっています。

REA-Video-Pro-Maxは、対応するスタイル要素を、確認・調整・再利用できる形にします。新しい台本、画像、映像、ナレーションを用意してください。最後に手元へ残るのは、編集可能なプロジェクトと実際にレンダリングされた動画です。

| 参考動画 A | あなたの新しい動画 B |
| :---: | :---: |
| [![自作の参考動画から取り出した実際のフレーム](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![新しい文章と独立した素材でレンダリングしたフレーム](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| ショットのリズムと字幕表現を調べる。 | 再利用できるスタイルで別の物語を描く。 |

*付属の自作デモから抽出した実際のフレームです。Bには新しいテキスト、独立して生成した素材、新しい字幕タイミングを使っています。[インタラクティブデモ](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace)では両動画をシークし、記録済みのタイムライン、テンプレート、プロジェクト、検証結果を確認できます。*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## 参考動画を、次の制作に活かす

| やりたいこと | 手に入るもの |
| --- | --- |
| 編集がその印象を生む理由を知る | 時刻と根拠に結びついたショット区間、見える文字、字幕の外観、見かけ上の動き、音声の手がかり。 |
| 字幕表現を新しい物語へ持ち込む | 新しい単語とタイミングに適用できる文字組み、配置、強調色のパレット。 |
| 繰り返し使える動画フォーマットを作る | 別の台本や素材に紐付けられるスタイルテンプレート。 |
| 結果を自分で調整する | 素材のコピーとハッシュを含み、確認・変更・再レンダリングできるネイティブJSONタイムライン／プロジェクト。 |
| 分析を自分のパイプラインに組み込む | 構造化ファイル、オフラインの分析ビューア、字幕出力、対応範囲が明確なタイムライン交換形式。 |

新製品紹介、教育動画、クリエイターの連載、編集研究、独自の動画ツールに。分析だけが必要なら、分析ファイルとタイムライン自体を成果物として受け取れます。

## ひとつのプロンプトで、制作を始める

同梱スキルをインストールし、参考動画と新しいコンテンツをエージェントに渡して、次のように依頼してください。

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

物語を決めるのは、あなたです。スキルは分析、構成、レンダリング、検証を進める具体的な手順と実行ツールをエージェントに提供します。

## 制作で役立つ、具体的な強み

- **根拠をたどれる編集分析。** デコードした表示タイムスタンプ、フレームの証拠、分析範囲からタイムラインを追跡できます。測定信号、モデルの結果、推定した編集判断は区別して記録します。
- **次の動画へ引き継げる字幕の細部。** 見える文字サイズ、位置、塗り、縁取りを推定し、観察した強調パレットやスタイルの違いを保持。構成時に新しい単語を組み直し、タイミングを付け直します。
- **方向まで扱うモーション。** 範囲を制限した相似／アフィン変換と時間曲線の候補をフィット。ネイティブレンダラーはズームアウトを含む、対応した方向付きズーム成分を再利用できます。
- **育てていけるプロジェクト。** 新しい画像、映像、フォント、任意の音声をポータブルなプロジェクトへコピーします。明示的な紐付けとハッシュで、選択したコンテンツを確認できます。
- **必要なときだけ音声認識。** 任意のローカルfaster-whisper ASRが、モデル由来の単語区間を提供します。台本と音声の厳密な照合により、新しいコンテンツへ紐付けられます。ローカルモデルの明示的な準備が必要です。
- **完成後に確かめられる結果。** プロジェクトと出力の同一性を検査し、レンダリング動画をデコードし、別途OCRで字幕内容を確認。根拠も出力と一緒に残せます。

ネイティブレンダラーは、**static / fade / pop / slide字幕**、**cut / dissolve / fade / wipeトランジション**、**static / 方向付きpanzoom背景**に対応します。分析は、ネイティブレンダラーで再現できる範囲より豊かなモーション観察を保持できます。[正確な対応範囲（英語）](docs/SUPPORT-MATRIX.md)。

## 最初の結果を作る

### 1. 実行環境を準備

**Python 3.11+**、**FFmpeg + FFprobe**、**libx264**を含むFFmpegビルドを使用します。付属のOCR・字幕検証の例には、**`eng`言語データ付きのTesseract**が必要です。Python依存関係は以下でインストールします。

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

これらのシェルコマンドはmacOS/Linux向けです。リリースCIはLinuxとmacOSで通過済みですが、Windowsのネイティブレンダリングは認証していません。`doctor`は、実際にマシンで利用できるツールを表示します。

### 2. エージェントにスキルを追加

`skills/rea-video-pro-max`フォルダを**丸ごと**、プロジェクトのスキルディレクトリへコピーします。

| ホスト | プロジェクト内の配置先 |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

[スキルZIP](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip)をそこへ展開しても構いません。`lib`、`assets`、`scripts`、`references`は一緒に保ってください。ZIPのみで導入する場合は、`python -m pip install -r /path/to/rea-video-pro-max/requirements.txt`でPython依存関係をインストールし、`python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`を起動点にします。以下のコンソールコマンドは、前述のチェックアウトからのインストールで利用できます。エージェントは、その依存関係が入ったインタープリターを使う必要があります。

### 公開動画 URL を自動で解析する

利用を許可された公開 YouTube、Facebook、TikTok の動画ページなら、任意の URL 取り込み機能を追加して、制限付きのローカルコピーを取得してから解析できます。

```sh
python -m pip install 'rea-video-pro-max[url]'
rea-video-pro-max analyze-url 'https://www.youtube.com/shorts/VIDEO_ID' --out work/url-analysis --ocr required --ocr-lang eng
```

展開した skill ZIP を使う場合は `yt-dlp>=2025.01.15,<2027` を直接インストールしてください。ZIP は任意の依存関係を自動でインストールしません。

上記の v0.1.1 skill ZIP はこの任意の URL アダプターより前のものです。次のリリースまでは現在の checkout を使用してください。

このコマンドは動画と、URL・抽出器・長さ・バイト数・SHA-256 を記録した `url-source.json` を保存し、通常の解析結果を `work/url-analysis/analysis/` に作成します。認証情報を使わず、DRM を回避せず、プレイリスト/ライブ配信やモデルの自動ダウンロードも受け付けません。プラットフォームへのアクセス権、著作権、利用規約は利用者が確認してください。[URL 取り込みの詳細（英語）](skills/rea-video-pro-max/references/url-ingestion.md)。

### 3. 付属のA → Bサンプルを実行

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

`work/video-b.mp4`を開いてください。ポータブルなプロジェクトは`work/project/`、参考動画の分析は`work/analysis/`にあります。構成のたびに新しい出力ディレクトリを使います。オフライン分析ビューアを作るには、次を実行します。

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

続いて`work/report/timeline.html`をローカルで開きます。[CLI、スキル、任意のMCPは同じカーネルを共有します（英語）](skills/rea-video-pro-max/references/runtime-and-support.md)。

<details>
<summary><strong>自分の作品にする：コンテンツバインディングとは？</strong></summary>

コンテンツバインディングは、新しいシーン、文章、素材、任意の音声／フォントを指定するJSONファイルです。エージェントは通常の制作依頼から作成できます。[examples/content.json](examples/content.json)を出発点にしてください。

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 24,
  "scenes": [
    {
      "id": "intro",
      "text": "Your next story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

画像や動画には`asset`のパスを、サウンドトラックやナレーションには`audio`を明示します。素材パスはこのJSONファイルを基準に解決します。レンダラーは選んだ新しいコンテンツを使い、参考動画と同一の素材を再利用するには明示的なオプトインが必要です。

新しい単語には新しいタイミングを割り当てます。文字数に重み付けしたタイミングは推定です。発話タイミングが重要な場合は新しい単語区間を指定するか、厳密に照合したローカルASRを使います。[音声とモーションのガイド（英語）](skills/rea-video-pro-max/references/speech-and-motion.md)。

</details>

## 約束を支える、実際の検証

**v0.1.1は176件のローカルテストを通過しました。** 実際の任意ローカルASRケースも含みます。[ホスティングCIのLinux/macOSジョブ3件も成功しました](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397)。アップロード済みのリリース成果物6点はダウンロードし、ローカルのバイト列とチェックサムに照合済みです。

根拠には、自作素材による完全な**A → 分析 → スタイル → 新しいB**の再実行、文字組み／縁取りと2種類の強調表現を確認した独立したベトナム語タスク、ズームイン／ズームアウトの方向を保持するモーションタスクが含まれます。いずれも範囲を限定した自作ケースです。実演したワークフローを示すもので、広範なジャンルや言語の精度を示すものではありません。

[分析データ](docs/evidence/reference-analysis.json) · [テンプレート](docs/evidence/style-template.json) · [プロジェクト](docs/evidence/project.json) · [検証結果](docs/evidence/verification.json) · [検証の詳細（英語）](docs/VALIDATION.md)

## 出力を手元に。システムをその先へ。

| 形式 | 内容 |
| --- | --- |
| ネイティブJSON | 分析、タイムライン、字幕／スタイル／モーション／音声データ、テンプレート、編集可能なネイティブプロジェクト。 |
| CSV | 確認や後続処理のためのショット行。 |
| SRT / WebVTT | 見えるテキストとキュー区間。 |
| ASS | 明示的な代替スタイルを用いた字幕タイミング。観察した外観と不確実性はネイティブの根拠に残します。 |
| OTIO / EDL | 任意のOTIO参考区間と注釈、測定した整数CFRカット向けEDL。出力記録で情報損失を説明します。 |
| MP4 + オフラインHTML | 新しい動画と、ローカルで確認できる分析レポート。 |

ネイティブプロジェクトは編集可能なJSONです。このリリースはPremiere、Resolve、After Effects、CapCut固有のプロジェクトやFCPXMLを出力しません。対応する交換形式ファイルの外部エディターへのインポートも未検証です。[エクスポーターとレンダラーの範囲（英語）](docs/SUPPORT-MATRIX.md)。

## 制作で知っておきたい範囲

現行リリースは、観察できる編集の根拠と、対応する**2D**スタイルの再利用に集中しています。正確な元フォント、隠れたレイヤー、プラグイン、元素材、プロジェクト履歴は不明のまま残る場合があります。OCRやモーションのフィットは誤ることがあり、サンプリング範囲と不確実性を明示します。

紐付ける映像は正しい向きで、正方形ピクセルである必要があります。シーン映像の音声はミュートされるため、音声は明示的に指定します。複雑な文字体系には適切なフォントとシェーピングが必要で、双方向字幕は拒否します。9言語のREADMEは製品説明の翻訳であり、9言語のOCR／レンダリング認証ではありません。創作スタイルと音の判断には人による確認が必要です。[全対応表（英語）](docs/SUPPORT-MATRIX.md)。

コア処理はローカルで動作し、有料モデルAPIやコンテンツのアップロードは不要です。依存関係や任意モデルの準備にはネットワークが必要な場合があり、Claude/Codexホストには独自のデータポリシーがあります。ローカルレポートには既定で参考メディアと切り抜きが含まれます。`report --no-media`は参考動画全体のコピーを省きますが、テキストと切り抜きは残ります。[プライバシー（英語）](docs/PRIVACY.md)。

## 次の編集ワークフローを、一緒に作ろう

**このワークフローを創作道具に加えたいと思ったら、ぜひStarを。** 他のクリエイターやAI開発者が、このプロジェクトを見つけるきっかけになります。

**Forkして、自分の編集言語を育ててください。** 字幕表現の追加、レンダラーアダプターの開発、出力フローの拡張、自作の参考動画と成果物の例など。再現可能な根拠とともに、次の機能を形にしましょう。

[**⭐ GitHubでStar**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Forkして作る**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [貢献ガイド（英語）](CONTRIBUTING.md) · [タスクを報告](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

[JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video)に着想を得た独立プロジェクトです。[Apache-2.0](LICENSE)。フォント、コーデック、モデルの別個の条件は[NOTICE](NOTICE)に保持しています。

[サポート（英語）](SUPPORT.md) · [保守方針（英語）](docs/MAINTENANCE.md) · [スキルの手順（英語）](skills/rea-video-pro-max/SKILL.md)
