---
name: gpt-bridge
description: 선생님의 ChatGPT(OpenAI) 구독을 Codex CLI로 연결해 GPT Image(ChatGPT Images 2.5)로 그림을 만든다. OpenAI API 키는 필요 없다. "그림 만들어줘", "이미지 생성해줘", "삽화 그려줘", "학습지에 넣을 그림 만들어줘", "GPT로 이미지 만들어줘", "gpt bridge", "이 그림 고쳐줘" 같은 요청이 오면 이 스킬을 사용한다. 수업 자료·학습지·시험지·안내문에 넣을 삽화, 모식도, 아이콘, 표지 그림을 만들거나 기존 그림을 바꿀 때 쓴다. 차트·그래프처럼 데이터로 정확히 그려야 하는 것은 이 스킬이 아니라 코드로 그린다.
---

# GPT bridge (ChatGPT 구독으로 이미지 생성)

Claude가 직접 그림을 그리는 대신, 선생님의 ChatGPT 구독으로 로그인한 **Codex CLI**에게 그림을 맡기는 다리(bridge)다.
`codex exec`가 Codex 내장 `image_gen` 도구를 부르고, 만들어진 PNG를 원하는 위치로 복사한다.

- 요금: API 요금이 아니라 ChatGPT 구독(Plus/Pro/Team 등) 사용량으로 처리된다.
- 모델: Codex가 계정에 제공하는 최신 이미지 모델을 쓴다(2026년 9월부터 ChatGPT Images 2.5가 Codex에 배포됨). 구독 방식에서는 모델 이름을 직접 고를 수 없다. 사용자에게 "2.5로 고정했다"고 말하지 않는다.

## 0. 준비 확인 (처음 한 번, 또는 새 세션마다)

1. `codex --version` 이 실패하면 설치한다: `npm install -g @openai/codex`
2. `codex login status` 가 "Logged in using ChatGPT" 가 아니면 로그인이 필요하다.
   - `codex login --device-auth` 를 **백그라운드로** 실행하고 출력에 나온 주소와 코드를 선생님께 알려 드린다. 선생님이 휴대폰/PC 브라우저에서 그 주소에 들어가 코드를 넣고 ChatGPT 계정으로 승인하면 끝난다.
   - 로그인 정보는 `~/.codex/auth.json` 에 저장된다. 이 파일 내용을 출력하거나 저장소에 커밋하지 않는다. 비밀번호나 토큰을 채팅에 붙여 넣으라고 하지 않는다.
   - 클라우드 세션은 끝나면 사라지므로 새 세션에서는 다시 로그인해야 한다.
3. 클라우드 환경이면 네트워크 정책에서 `chatgpt.com`, `auth.openai.com` 이 허용되어야 한다. 막혀 있으면 스크립트가 알려 준다. 그때는 환경 설정(세션 제목 표시줄의 환경 메뉴 → Edit → Network access → Allowed domains)에 두 주소를 추가하고 새 세션을 열도록 안내한다.

준비가 안 되면 그림이 만들어지지 않았다는 사실을 그대로 알린다. 만든 척하거나 다른 그림으로 대신하지 않는다.

## 1. 절차

1. **요청 파악**: 무엇을 그릴지, 어디에 쓸지(학습지, PPT, 시험지 등), 가로/세로, 흑백/컬러를 확인한다. 분명하지 않은 것만 짧게 묻고 나머지는 알맞게 정한다.
2. **프롬프트 작성**: 한국어 요청을 영어 프롬프트로 다듬는다(아래 요령).
3. **실행** (한 장에 수 분 걸릴 수 있으니 Bash 타임아웃을 600000ms로 준다):
   ```bash
   python3 .claude/skills/gpt-bridge/scripts/gpt_image.py "<영어 프롬프트>" --out images/<파일이름>.png
   ```
   마지막 줄에 저장된 파일 경로가 나온다. 여러 장이 필요하면 프롬프트를 바꿔 여러 번 실행한다.
4. **전달**: 파일을 SendUserFile 로 보여 주고, 쓴 프롬프트를 한 줄로 알려 준다. 고칠 점을 말씀하시면 `--ref` 로 방금 그림을 넣어 수정하거나 프롬프트를 바꿔 다시 만든다.

## 2. 옵션

| 옵션 | 예시 | 언제 쓰나 |
|---|---|---|
| `--out` | `images/water_cycle.png` | 저장 위치·이름 (기본: `images/날짜_프롬프트.png`) |
| `--size` | `1536x1024`(가로), `1024x1536`(세로), `1024x1024` | PPT·가로 자료는 가로, A4 세로 자료는 세로. 4K가 필요하면 `3840x2160` |
| `--transparent` | | 아이콘·스티커처럼 배경 없이 붙일 그림 |
| `--ref` | `--ref 원본.png` (여러 번 가능) | 기존 그림을 고치거나, 참고 그림의 스타일을 따를 때 |
| `--effort` | `low`(기본), `medium` | Codex가 프롬프트를 다듬는 정도. 높을수록 느리다 |

크기·투명 배경은 Codex에 요청으로 전달되는 것이라 정확히 지켜지지 않을 수 있다.

## 3. 수업 자료용 프롬프트 요령

- **영어로 쓴다.** 모델이 영어 프롬프트를 더 정확히 따른다.
- **그림 속 글자는 최소로.** 최신 모델은 글자를 꽤 잘 쓰지만 한글은 여전히 틀릴 수 있다. 이름표가 많은 그림은 `no text, no labels` 로 만들고 한글 문서/PPT에서 붙이도록 권한다. 글자를 넣었다면 맞춤법을 꼭 확인하시라고 말한다.
- **용도에 맞는 스타일을 정한다.**
  - 교과서 삽화: `clean educational textbook illustration, simple flat style, white background`
  - 흑백 인쇄 학습지·시험지: `black and white line drawing, clear outlines, no shading, white background`
  - 모식도: `simple scientific diagram, minimal colors, empty label boxes`
  - PPT 표지: `bright, friendly illustration for a middle school class presentation`
- **과학적 정확성은 직접 확인한다.** 생성 그림은 구조·개수·위치가 틀릴 수 있다. 시험지에 넣을 그림은 선생님께 꼭 검토를 부탁드린다.
- 실제 인물이나 학생 얼굴처럼 보이는 그림, 저작권 캐릭터는 만들지 않는다.
