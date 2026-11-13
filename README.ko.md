# REA-Video-Pro-Max

## Claude와 Codex에 편집자의 눈을 더하세요.

**레퍼런스 영상의 템포, 자막, 움직임을 분석하세요. 편집의 선택을 재사용 가능한 스타일로 바꾸고, 나만의 글과 미디어로 새로운 영상을 렌더링하세요.**

좋은 편집에는 자신만의 언어가 있습니다. 이제 그 언어를 창작 도구로 만들어 보세요.

[**▶ 라이브 데모 살펴보기**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**스킬 다운로드**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [릴리스 v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Claude Code / Codex 스킬 · CLI + 선택형 MCP · 로컬 처리 · Apache-2.0**

---

## “이 편집 좋다”에서 “내 버전은 이거야”까지.

컷의 리듬, 자막이 등장하는 타이밍, 문장 속 강조 색상, 정지 이미지에 생동감을 주는 줌. 마음을 사로잡는 영상에는 이런 선택이 쌓여 있습니다.

REA-Video-Pro-Max는 지원되는 스타일 요소를 살펴보고, 조정하고, 재사용할 수 있는 데이터로 만듭니다. 새 대본, 이미지, 영상 또는 내레이션을 준비하세요. 결과로 편집 가능한 프로젝트와 실제 렌더링 영상을 가져갈 수 있습니다.

| 레퍼런스 A | 나만의 새 영상 B |
| :---: | :---: |
| [![자체 제작 레퍼런스 영상의 실제 프레임](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![새 문구와 별도 미디어로 렌더링한 프레임](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| 컷의 리듬과 자막 표현을 분석합니다. | 재사용 가능한 스타일로 다른 이야기를 만듭니다. |

*포함된 자체 제작 데모에서 추출한 실제 프레임입니다. B는 새 텍스트, 독립적으로 생성한 미디어, 새로운 자막 타이밍을 사용합니다. [인터랙티브 데모](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace)에서 두 영상을 탐색하고 기록된 타임라인, 템플릿, 프로젝트와 검증 결과를 확인할 수 있습니다.*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## 레퍼런스를 실제 작업에 활용하세요

| 하고 싶은 일 | 얻는 결과 |
| --- | --- |
| 편집이 특정한 느낌을 주는 이유 이해하기 | 타임스탬프와 근거가 연결된 샷 구간, 보이는 텍스트, 자막 외형, 겉으로 드러난 움직임과 오디오 단서. |
| 자막 표현을 새로운 이야기에 적용하기 | 새 단어와 새 타이밍에 맞춰 적용하는 타이포그래피, 배치, 강조 색상 팔레트. |
| 반복 제작할 영상 포맷 만들기 | 다른 대본과 에셋에 연결할 수 있는 스타일 템플릿. |
| 결과를 직접 조정하기 | 에셋 사본과 해시를 포함하고, 확인·수정·재렌더링할 수 있는 네이티브 JSON 타임라인/프로젝트. |
| 분석을 기존 파이프라인에 연결하기 | 구조화된 파일, 오프라인 검사 화면, 자막 내보내기, 지원 범위가 명확한 타임라인 교환 형식. |

제품 소개, 교육 영상, 크리에이터 시리즈, 편집 연구 또는 나만의 영상 도구에 활용하세요. 분석만 필요하다면 분석 파일과 타임라인 자체가 완성된 결과물입니다.

## 프롬프트 하나로 시작하는 워크플로

번들 스킬을 설치하고 에이전트에 레퍼런스와 새 콘텐츠를 제공한 뒤 다음과 같이 요청하세요.

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

이야기의 방향은 여러분이 정합니다. 스킬은 분석, 구성, 렌더링, 검증을 위한 구체적인 절차와 실행 도구를 에이전트에 제공합니다.

## 창작에 도움이 되는 실질적인 기능

- **근거를 따라가는 편집 분석.** 디코딩한 표시 타임스탬프, 프레임 근거와 분석 범위로 타임라인을 추적합니다. 측정 신호, 모델 결과, 추론한 편집 선택은 각각 구분해 표시합니다.
- **다음 영상까지 이어지는 자막 디테일.** 보이는 크기, 위치, 채움색, 외곽선을 추정하고 관찰된 강조 팔레트와 스타일 변형을 구분해 보존합니다. 구성 단계에서 새 단어의 줄바꿈과 타이밍을 다시 정합니다.
- **방향을 보존하는 움직임.** 제한된 범위의 유사/아핀 변환과 시간 곡선 후보를 피팅합니다. 네이티브 렌더러는 줌 아웃을 포함해 지원되는 줌 방향 성분을 재사용할 수 있습니다.
- **계속 발전시킬 수 있는 프로젝트.** 새 이미지, 영상, 폰트와 선택한 오디오를 이식 가능한 프로젝트에 복사합니다. 명시적인 연결과 해시로 선택한 콘텐츠를 확인할 수 있습니다.
- **필요할 때 사용하는 음성 분석.** 선택형 로컬 faster-whisper ASR이 모델에서 도출한 단어 구간을 제공합니다. 대본과 오디오를 엄격히 대조해 새 콘텐츠에 연결할 수 있으며, 로컬 모델을 명시적으로 준비해야 합니다.
- **확인할 수 있는 최종 결과.** 프로젝트와 출력의 동일성을 검사하고 렌더링 영상을 디코딩하며, 별도의 OCR로 자막 내용을 확인합니다. 근거도 결과물과 함께 보관하세요.

네이티브 렌더러는 **static / fade / pop / slide 자막**, **cut / dissolve / fade / wipe 전환**, **static / 방향이 있는 panzoom 배경**을 지원합니다. 분석에는 네이티브 렌더러가 재현하는 범위보다 풍부한 움직임 관찰값이 남을 수 있습니다. [정확한 지원 범위(영문)](docs/SUPPORT-MATRIX.md).

## 첫 결과 만들기

### 1. 실행 환경 준비

**Python 3.11+**, **FFmpeg + FFprobe**, **libx264**를 포함한 FFmpeg 빌드를 사용하세요. 포함된 OCR 및 자막 검증 예제를 실행하려면 **`eng` 언어 데이터가 설치된 Tesseract**가 필요합니다. Python 의존성은 아래에서 설치합니다.

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

위 셸 명령은 macOS/Linux용입니다. 릴리스 CI는 Linux와 macOS에서 통과했으며 Windows 네이티브 렌더링은 검증되지 않았습니다. `doctor`는 현재 컴퓨터에서 실제 사용할 수 있는 도구를 알려줍니다.

### 2. 에이전트에 스킬 추가

`skills/rea-video-pro-max` 폴더 **전체**를 프로젝트의 스킬 디렉터리에 복사하세요.

| 호스트 | 프로젝트 내부 설치 위치 |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

[스킬 ZIP](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip)을 같은 위치에 풀어도 됩니다. `lib`, `assets`, `scripts`, `references`를 함께 유지하세요. ZIP만 설치할 경우 `python -m pip install -r /path/to/rea-video-pro-max/requirements.txt`로 Python 의존성을 설치하며 진입점은 `python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`입니다. 아래 콘솔 명령은 앞서 저장소를 설치한 환경에서 제공됩니다. 에이전트는 해당 의존성이 설치된 인터프리터를 사용해야 합니다.

### 공개 동영상 URL 자동 분석

사용 권한이 있는 공개 YouTube, Facebook 또는 TikTok 동영상 페이지라면 선택적 URL 수집 기능을 설치해 제한된 로컬 사본을 받은 뒤 분석할 수 있습니다.

```sh
python -m pip install 'rea-video-pro-max[url]'
rea-video-pro-max analyze-url 'https://www.youtube.com/shorts/VIDEO_ID' --out work/url-analysis --ocr required --ocr-lang eng
```

추출한 skill ZIP을 사용하는 경우 `yt-dlp>=2025.01.15,<2027`를 직접 설치하세요. ZIP은 선택적 의존성을 자동으로 설치하지 않습니다.

위에 연결된 v0.1.1 skill ZIP은 이 선택적 URL 어댑터보다 먼저 배포되었습니다. 다음 릴리스 전에는 현재 checkout을 사용하세요.

이 명령은 동영상과 URL, 추출기, 길이, 바이트 수, SHA-256이 담긴 `url-source.json`을 저장한 뒤 `work/url-analysis/analysis/`에 일반 분석 결과를 만듭니다. 자격 증명을 사용하거나 DRM을 우회하지 않으며, 재생목록/라이브 스트림과 모델 가중치 다운로드를 허용하지 않습니다. 플랫폼 접근 권한, 저작권과 이용약관은 사용자가 확인해야 합니다. [URL 수집 상세(영어)](skills/rea-video-pro-max/references/url-ingestion.md).

### 3. 포함된 A → B 예제 실행

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

`work/video-b.mp4`를 여세요. 이식 가능한 프로젝트는 `work/project/`, 레퍼런스 분석은 `work/analysis/`에 저장됩니다. 구성할 때마다 새 출력 디렉터리를 사용하세요. 오프라인 분석 검사 화면을 만들려면 다음을 실행합니다.

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

이후 로컬에서 `work/report/timeline.html`을 여세요. [CLI, 스킬, 선택형 MCP는 같은 커널을 사용합니다(영문)](skills/rea-video-pro-max/references/runtime-and-support.md).

<details>
<summary><strong>내 콘텐츠로 만들기: 콘텐츠 바인딩에는 무엇이 들어가나요?</strong></summary>

콘텐츠 바인딩은 새 장면, 텍스트, 미디어와 선택형 오디오/폰트를 지정하는 JSON 파일입니다. 에이전트가 평범한 작업 요청을 바탕으로 작성할 수 있습니다. [examples/content.json](examples/content.json)에서 시작하세요.

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

이미지나 영상은 `asset` 경로로, 사운드트랙이나 내레이션은 `audio`로 명시합니다. 미디어 경로는 이 JSON 파일을 기준으로 해석됩니다. 렌더러는 선택한 새 콘텐츠를 사용합니다. 레퍼런스와 정확히 같은 미디어를 재사용하려면 명시적인 동의가 필요합니다.

새 단어에는 새로운 타이밍이 부여됩니다. 문자 수에 비례한 타이밍은 추정값입니다. 음성 타이밍이 중요하다면 새 단어 구간을 제공하거나 엄격히 대조한 로컬 ASR을 사용하세요. [음성과 움직임 가이드(영문)](skills/rea-video-pro-max/references/speech-and-motion.md).

</details>

## 약속을 뒷받침하는 실제 결과

**v0.1.1은 176개의 로컬 테스트를 통과했습니다.** 실제 선택형 로컬 ASR 사례도 포함됩니다. [호스팅 CI의 Linux/macOS 작업 3개도 통과했습니다](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397). 업로드된 릴리스 아티팩트 6개를 다운로드해 로컬 바이트와 체크섬에 대조했습니다.

근거에는 자체 제작 **A → 분석 → 스타일 → 새로운 B** 전체 재실행, 타이포그래피/외곽선을 보정하고 두 강조 표현을 확인한 독립적인 베트남어 작업, 줌 인/줌 아웃 방향을 보존한 움직임 작업이 포함됩니다. 이는 범위가 한정된 자체 제작 사례로 해당 워크플로를 입증하며, 광범위한 장르나 언어 정확도를 뜻하지는 않습니다.

[분석 데이터](docs/evidence/reference-analysis.json) · [템플릿](docs/evidence/style-template.json) · [프로젝트](docs/evidence/project.json) · [검증 결과](docs/evidence/verification.json) · [검증 상세(영문)](docs/VALIDATION.md)

## 결과를 소유하고, 시스템을 확장하세요

| 형식 | 포함되는 내용 |
| --- | --- |
| 네이티브 JSON | 분석, 타임라인, 자막/스타일/움직임/오디오 데이터, 템플릿, 편집 가능한 네이티브 프로젝트. |
| CSV | 검사와 후속 처리를 위한 샷 행. |
| SRT / WebVTT | 보이는 텍스트와 큐 구간. |
| ASS | 명시적인 대체 스타일을 적용한 자막 타이밍. 관찰된 외형과 불확실성은 네이티브 근거에 보존됩니다. |
| OTIO / EDL | 선택형 OTIO 레퍼런스 구간과 주석, 측정된 정수 CFR 컷을 위한 EDL. 내보내기 기록에 손실을 명시합니다. |
| MP4 + 오프라인 HTML | 새 영상과 로컬에서 살펴볼 수 있는 분석 보고서. |

네이티브 프로젝트는 편집 가능한 JSON입니다. 이 릴리스는 Premiere, Resolve, After Effects, CapCut의 고유 프로젝트 형식이나 FCPXML을 내보내지 않습니다. 지원되는 교환 파일을 외부 편집기로 가져오는 과정도 아직 검증되지 않았습니다. [내보내기/렌더러의 범위(영문)](docs/SUPPORT-MATRIX.md).

## 창작 전에 알아둘 범위

현재 릴리스는 관찰 가능한 편집 근거와 지원되는 **2D** 스타일 재사용에 집중합니다. 정확한 원본 폰트, 숨겨진 레이어, 플러그인, 원본 에셋과 프로젝트 이력은 알 수 없는 상태로 남을 수 있습니다. OCR과 움직임 피팅은 틀릴 수 있으며 샘플링 범위와 불확실성을 함께 표시합니다.

연결할 영상은 올바른 방향이며 정사각 픽셀이어야 합니다. 장면 영상의 오디오는 음소거되므로 오디오는 별도로 지정하세요. 복잡한 문자는 적합한 폰트와 조판 지원이 필요하며 양방향 자막은 거부됩니다. README의 9개 번역은 제품 문서이며 9개 OCR/렌더링 언어를 검증했다는 뜻이 아닙니다. 창작 스타일과 사운드의 평가는 사람이 검토해야 합니다. [전체 지원 표(영문)](docs/SUPPORT-MATRIX.md).

핵심 처리는 로컬에서 실행되며 유료 모델 API나 콘텐츠 업로드가 필요하지 않습니다. 의존성과 선택형 모델 준비에는 네트워크가 필요할 수 있으며 Claude/Codex 호스트는 자체 데이터 정책을 따릅니다. 로컬 보고서에는 기본적으로 레퍼런스 미디어와 크롭이 포함됩니다. `report --no-media`는 전체 레퍼런스 사본을 제외하지만 텍스트와 크롭은 남깁니다. [개인정보 처리(영문)](docs/PRIVACY.md).

## 다음 편집 워크플로를 함께 만드세요

**이 워크플로를 창작 도구에 추가하고 싶다면 프로젝트에 별을 남겨 주세요.** 다른 크리에이터와 AI 개발자가 이 작업을 발견하는 데 도움이 됩니다.

**포크해서 나만의 편집 언어를 만드세요.** 자막 표현을 추가하고, 렌더러 어댑터를 개발하고, 내보내기 흐름을 확장하거나 직접 제작한 레퍼런스와 결과 사례를 기여할 수 있습니다. 재현 가능한 근거와 함께 다음 기능을 발전시켜 주세요.

[**⭐ GitHub에서 Star**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Fork하고 만들기**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [기여 안내(영문)](CONTRIBUTING.md) · [작업 제보](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

[JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video)에서 영감을 받은 독립 프로젝트입니다. [Apache-2.0](LICENSE); 폰트, 코덱, 모델의 별도 조건은 [NOTICE](NOTICE)에 보존되어 있습니다.

[지원(영문)](SUPPORT.md) · [유지보수(영문)](docs/MAINTENANCE.md) · [스킬 지침(영문)](skills/rea-video-pro-max/SKILL.md)
