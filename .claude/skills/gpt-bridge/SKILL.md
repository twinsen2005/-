---
name: gpt-bridge
description: OpenAI GPT 이미지 모델(gpt-image)로 그림을 생성한다. "그림 만들어줘", "이미지 생성해줘", "삽화 그려줘", "학습지에 넣을 그림 만들어줘", "GPT로 이미지 만들어줘", "gpt bridge" 같은 요청이 오면 이 스킬을 사용한다. 수업 자료·학습지·시험지·안내문에 넣을 삽화, 모식도, 아이콘, 표지 그림 등을 만들 때 쓴다. 차트·그래프처럼 데이터로 정확히 그려야 하는 것은 이 스킬이 아니라 코드로 그린다.
---

# GPT bridge (이미지 생성)

OpenAI 이미지 API를 호출해 PNG 파일을 만드는 스킬이다. 선생님의 수업 자료에 들어갈 그림을 만드는 데 맞춰져 있다.

## 사전 조건

- 환경 변수 `OPENAI_API_KEY` 가 있어야 한다.
- 클라우드 환경의 네트워크 정책에서 `api.openai.com` 이 허용되어 있어야 한다.

둘 중 하나라도 없으면 스크립트가 한국어로 원인을 알려 준다. 그 메시지를 선생님께 그대로 전달하고, 환경 설정(세션 제목 표시줄의 환경 메뉴 → Edit)에서 고치는 방법을 안내한다. API 키를 채팅에 붙여 넣으라고 하지 않는다. 그림이 만들어지지 않았는데 만든 척하거나 다른 그림으로 대신하지 않는다.

## 절차

1. **요청 파악**: 무엇을 그릴지, 어디에 쓸지(학습지, PPT, 시험지 등), 가로/세로, 장수를 확인한다. 분명하지 않은 것만 짧게 묻고, 나머지는 아래 기본값을 쓴다.
2. **프롬프트 작성**: 선생님의 한국어 요청을 영어 프롬프트로 다듬는다(아래 작성 요령 참고).
3. **실행**:
   ```bash
   python3 .claude/skills/gpt-bridge/scripts/generate_image.py "<영어 프롬프트>" --out images/<파일이름>.png
   ```
   이미지 생성은 수십 초에서 1~2분 걸릴 수 있으므로 Bash 타임아웃을 넉넉히(300000ms) 준다.
4. **전달**: 출력된 파일 경로를 SendUserFile 로 보여 주고, 사용한 프롬프트를 한 줄로 알려 준다. 고칠 점을 말씀하시면 프롬프트를 수정해 다시 만든다.

## 옵션

| 옵션 | 값 | 기본값 | 언제 쓰나 |
|---|---|---|---|
| `--size` | `1024x1024`, `1536x1024`(가로), `1024x1536`(세로), `auto` | `1024x1024` | PPT·가로 학습지는 가로, A4 세로 자료는 세로 |
| `--quality` | `low`, `medium`, `high`, `auto` | `medium` | 시안은 `low`, 최종본·인쇄용은 `high` |
| `-n` | 1~4 | 1 | 여러 시안 중에 고를 때 |
| `--transparent` | (플래그) | 꺼짐 | 아이콘·스티커처럼 배경 없이 붙일 그림 |
| `--model` | 모델 이름 | `OPENAI_IMAGE_MODEL` 또는 `gpt-image-1` | 다른 모델을 쓰고 싶을 때 |
| `--out` | 파일 경로 | `images/날짜_프롬프트.png` | 파일 이름을 정할 때 |

## 수업 자료용 프롬프트 작성 요령

- **영어로 쓴다.** 모델이 영어 프롬프트를 더 정확히 따른다.
- **그림 속 글자는 피한다.** 한글은 깨지거나 엉뚱하게 나오기 쉽다. 프롬프트에 `no text, no labels` 를 넣고, 이름표·설명은 한글 문서나 PPT에서 따로 붙이도록 안내한다. 꼭 글자가 필요하면 짧은 영어 단어만 넣는다.
- **용도에 맞는 스타일을 정한다.**
  - 교과서 삽화: `clean educational textbook illustration, simple flat style, white background`
  - 흑백 인쇄 학습지·시험지: `black and white line drawing, clear outlines, no shading, white background`
  - 모식도: `simple scientific diagram, labeled parts left blank, minimal colors`
  - PPT 표지: `bright, friendly illustration for a middle school class presentation`
- **과학적 정확성은 직접 확인한다.** 생성 그림은 구조나 개수가 틀릴 수 있다(예: 꽃잎 수, 기관 위치). 시험지에 넣을 그림은 선생님께 꼭 검토를 부탁드린다고 말한다.
- 실제 인물이나 학생 사진처럼 보이는 그림은 만들지 않는다.
