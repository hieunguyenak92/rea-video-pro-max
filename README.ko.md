# REA-Video-Pro-Max

## 편집 방식을 분석하고, 그 스타일로 새로운 영상을 만드세요.

**참고 영상을 근거가 연결된 타임라인과 재사용 가능한 스타일 템플릿으로 바꿉니다. 다른 대본과 미디어를 연결해 나만의 영상을 렌더링하세요.**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[기록된 데모](docs/index.html) · [영상 A](docs/media/reference.mp4) · [영상 B](docs/media/adapted.mp4) · [검증 기록 (English)](docs/VALIDATION.md)

좋은 편집에는 컷의 위치, 자막 묶음, 강조되는 단어, 동작의 마무리와 사운드 타이밍 같은 결정이 담겨 있습니다. REA-Video-Pro-Max는 지원되는 결정들을 살펴보고 재사용할 수 있게 합니다.

```text
영상 A → 분석 + 추론 타임라인 → 스타일 템플릿 + 새 콘텐츠 → 편집 가능한 프로젝트 → 영상 B
```

데모는 프로젝트가 소유한 합성 미디어를 사용합니다. A와 B의 텍스트와 미디어는 다릅니다. 정적 사이트는 기록된 결과를 보여 주며, 실시간 추론이나 방문자 영상 업로드를 수행하지 않습니다.

## 어떤 작업에 사용할 수 있나요?

- 영상 전체의 쇼트, 자막 스타일, 모션, 오디오 큐와 타임라인을 타임스탬프 근거와 함께 분석합니다.
- 한 프레임의 타이포그래피, 레이아웃과 색상을 조사합니다. 한 장의 이미지만으로 동작 시간이나 사운드를 알 수는 없습니다.
- 분석한 스타일에 새 대본, 이미지 또는 촬영 영상을 연결해 다른 영상을 만듭니다.
- 분석만 요청했다면 타임라인과 분석 파일을 독립적인 결과로 받을 수 있습니다.

```text
REA-Video-Pro-Max로 reference.mp4의 타임라인과 스타일을 분석하세요. 새 대본과 내 자산으로 비슷한 자막, 모션, 편집 리듬의 다른 영상을 만드세요. 템플릿, 프로젝트, 렌더링 결과와 미검증 부분을 제공하세요.
```

## 첫 결과 만들기

Python 3.11+, FFmpeg, FFprobe가 필요합니다. Python 런타임은 Pillow, NumPy, PyAV를 사용합니다. OCR용 Tesseract는 선택 사항이며 설치한 언어 데이터에 따라 사용 가능한 언어가 달라집니다. 정확한 검증 범위는 [지원 표 (English)](docs/SUPPORT-MATRIX.md)를 확인하세요.

macOS는 실제 측정한 개발 플랫폼입니다. Linux는 예정된 CI 대상이며 Windows 네이티브 렌더러는 인증되지 않았습니다. 생성 검증은 정확한 렌더 기록 해시와 독립 OCR 검사를 요구하므로 전체 예제에는 Tesseract와 `eng` 데이터가 필요합니다.

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

명령은 Git 체크아웃 구조를 기준으로 합니다. 압축 해제한 스킬 폴더에서는 `scripts/rea-video-pro-max.py`를 사용하고 `lib`, `assets`, `references`를 함께 유지하세요. 의존성이 설치된 Python을 사용하며 진입점 파일만 복사하지 마세요.

## 새 콘텐츠 연결하기

`examples/content.json`은 content binding의 합성 예제입니다. 새 장면에는 `id`, `text`, `duration`, `background`, `accent`와 선택적인 `asset` 경로가 들어갑니다. `width`, `height`, `fps`는 출력 설정이며 `audio`와 `font`도 선택할 수 있습니다. 미디어 경로는 바인딩 파일을 기준으로 해석합니다. 프로젝트는 자산과 해시를 기록하며 A의 영상이나 음악을 조용히 재사용하지 않습니다. 새 발화에는 새 타이밍이 필요하고, 정확한 정렬이 없을 때는 추정 방법을 명시합니다.

장면 영상의 오디오는 음소거됩니다. 사운드는 새 `audio` 바인딩으로 별도 제공하세요. 짧은 영상은 마지막 프레임을 유지하며 네이티브 입력 영상은 정방향·정사각 픽셀이어야 합니다. CSV는 쇼트 행만 내보냅니다. 복잡하거나 양방향 문자는 조판·묶음 지원 범위를 먼저 확인하세요.

## Claude Code / Codex에서 사용

`skills/rea-video-pro-max` 폴더 전체를 호스트의 스킬 디렉터리에 복사하거나 에이전트에게 체크아웃에서 설치하도록 요청하세요. 프로젝트 위치는 보통 `.claude/skills/rea-video-pro-max` 또는 `.agents/skills/rea-video-pro-max`입니다. 스킬 설치로 FFmpeg, OCR 언어 또는 모델 가중치가 설치되지는 않습니다. 호스트 계정, 실행 권한, 데이터 정책은 별개입니다. [스킬 지침](skills/rea-video-pro-max/SKILL.md)과 기술 문서는 English로 제공됩니다.

## 파일과 내보내기

- Native JSON은 분석, 타임라인, 자막·스타일·모션·오디오, 템플릿과 프로젝트 정보를 보존합니다. CSV는 편집 데이터 검토에 사용합니다.
- SRT/WebVTT/ASS는 각 형식이 지원하는 텍스트와 타이밍을 내보냅니다. SRT는 전체 타이포그래피나 모션을 보존하지 않습니다.
- 설치 버전에서 available로 보고한 타임라인 어댑터만 사용하세요. 내보내기 기록은 지원 범위, 근사값과 손실을 표시하며 모든 편집기의 효과 재현을 보장하지 않습니다.
- 소프트웨어 렌더러는 새 콘텐츠를 구성하고 FFmpeg로 인코딩합니다. FFmpeg의 선택적 `drawtext`, `ass`, `subtitles` 필터는 필요하지 않습니다.

## 중요한 제한

측정된 메타데이터, OCR 결과, 스타일 추정, 제작 방식 가설은 서로 다른 근거입니다. 평면화된 영상에서 원본 소스, 숨겨진 레이어, 정확한 폰트·플러그인·편집 프로젝트나 AI 프롬프트를 유일하게 복원할 수는 없습니다. 초기 범위는 타이밍, 자막과 지원되는 2D 요소입니다. 범용 디컴파일러나 검증된 시장 최고 제품이 아닙니다. 복잡한 가림, 3D, HDR 마스터링과 임의 NLE 왕복은 검증 범위 밖입니다. 복잡한 문자 조판은 별도의 지원과 테스트가 필요하며 README 번역 수가 OCR·렌더 언어 인증을 뜻하지 않습니다.

영상 B는 새 콘텐츠, 스타일 계약과 재생 상태로 검증합니다. A와의 전체 프레임 픽셀 일치가 기준이 아닙니다. 기술 검증과 사람의 창작 품질 평가는 구분합니다. [검증과 제한 (English)](docs/VALIDATION.md).

## 로컬 처리와 출처

코어는 로컬에서 실행되며 유료 API, 호스팅 추론 업로드 또는 자동 게시가 필요하지 않습니다. 의존성 설치와 선택적 제공자는 네트워크를 사용할 수 있습니다. Claude/Codex 호스트 정책은 별개입니다. [Privacy (English)](docs/PRIVACY.md). JuneYaooo/rea-video에서 영감을 받은 독립 제품으로 공식 업그레이드가 아닙니다. 소스·폰트·미디어·코덱·모델의 약관은 각각 적용됩니다.

로컬 보고서는 기본적으로 참고 영상과 근거 파일을 복사합니다. `report --no-media`는 전체 미디어 복사만 생략하며 OCR 텍스트, 로컬 경로와 크롭은 남습니다. 공유 전에 확인하세요.

[지원 (English)](SUPPORT.md) · [유지보수 (English)](docs/MAINTENANCE.md) · 번역은 전문 원어민 검수를 받았다고 주장하지 않습니다.

[로컬 음성 및 고급 모션 (영어 기술 문서)](skills/rea-video-pro-max/references/speech-and-motion.md).
