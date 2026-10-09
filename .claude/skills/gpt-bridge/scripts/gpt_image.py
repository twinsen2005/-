#!/usr/bin/env python3
"""GPT bridge: ChatGPT 구독(Codex CLI 로그인)으로 GPT Image 그림을 만든다.

OpenAI API 키 없이, `codex login` 으로 로그인한 ChatGPT 계정의 내장 image_gen
도구를 `codex exec` 로 불러 PNG를 만들고 원하는 경로로 복사한다.
어떤 이미지 모델(GPT Image 2.5 등)을 쓸지는 Codex(ChatGPT 계정)가 정한다.

사용 예:
    python3 gpt_image.py "광합성 과정 교과서 삽화, 흑백 선화" --out images/photosynthesis.png
    python3 gpt_image.py "물의 순환 모식도" --size 1536x1024
    python3 gpt_image.py "이 그림을 흑백 선화로 바꿔줘" --ref 원본.png --out images/line.png

표준 라이브러리만 사용한다. 필요한 것: codex CLI(npm install -g @openai/codex), codex login.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TIMEOUT_SEC = 900
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def fail(message, log_text=None):
    print(f"[gpt-bridge] 오류: {message}", file=sys.stderr)
    if log_text:
        tail = "\n".join(log_text.strip().splitlines()[-30:])
        print(f"--- codex 로그 마지막 부분 ---\n{tail}", file=sys.stderr)
    sys.exit(1)


def default_out_path(prompt):
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", prompt).strip("_")[:30] or "image"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("images") / f"{stamp}_{slug}.png"


def check_codex():
    if not shutil.which("codex"):
        fail("codex CLI가 없습니다. `npm install -g @openai/codex` 로 설치한 뒤 `codex login` 하세요.")
    status = subprocess.run(["codex", "login", "status"], capture_output=True, text=True)
    text = (status.stdout + status.stderr).strip()
    if status.returncode != 0 or "not logged in" in text.lower():
        fail(
            "Codex에 ChatGPT 계정으로 로그인되어 있지 않습니다. "
            "`codex login --device-auth` 를 실행하고, 나온 주소에서 코드를 입력해 로그인하세요."
        )
    if "api key" in text.lower():
        print("[gpt-bridge] 주의: ChatGPT 구독이 아니라 API 키로 로그인되어 있습니다. API 요금이 청구될 수 있습니다.", file=sys.stderr)


def build_prompt(prompt, size, transparent, has_ref):
    lines = [
        "Use your built-in image_gen tool to create an image.",
        "",
        f"PROMPT: {prompt}",
    ]
    if size:
        lines.append(f"SIZE: {size}")
    if transparent:
        lines.append("BACKGROUND: genuinely transparent background (keep the alpha channel).")
    if has_ref:
        lines.append("Use the attached image(s) as the reference / image to edit.")
    lines += [
        "",
        "Requirements:",
        "- You MUST call the built-in image_gen tool. Do NOT write a script, call an API, or draw the PNG any other way.",
        "- Do NOT ask follow-up questions; make reasonable choices yourself.",
        "- After the tool produces the image, copy it to out.png in your current working directory (relative path out.png).",
        "- Reply with only the file name of the saved image, nothing else.",
    ]
    return "\n".join(lines)


def list_images(folder):
    if not folder.is_dir():
        return set()
    return {p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS}


def newest_new_image(folder, existing):
    found = list_images(folder) - existing
    return max(found, key=lambda p: p.stat().st_mtime, default=None)


def explain_failure(log_text):
    low = log_text.lower()
    if "403" in low or "forbidden" in low or "tunnel" in low or ("connect" in low and "denied" in low):
        return (
            "네트워크 정책이 OpenAI 접속을 막은 것 같습니다. "
            "환경 설정 > Network access 의 Allowed domains 에 chatgpt.com 과 auth.openai.com 을 추가하세요."
        )
    if "401" in low or "unauthorized" in low or ("login" in low and "expired" in low):
        return "로그인이 만료되었습니다. `codex login --device-auth` 로 다시 로그인하세요."
    if "usage limit" in low or "rate limit" in low or "429" in low:
        return "ChatGPT 구독의 사용 한도에 걸렸습니다. 잠시 뒤에 다시 시도하세요."
    return "원인은 아래 codex 로그를 확인하세요."


def main():
    parser = argparse.ArgumentParser(description="ChatGPT 구독(Codex)으로 GPT Image 그림 생성")
    parser.add_argument("prompt", help="그림 설명 (영어가 보통 더 정확합니다)")
    parser.add_argument("--out", type=Path, help="저장할 경로 (기본: images/날짜_프롬프트.png)")
    parser.add_argument("--size", help="원하는 크기, 예: 1024x1024, 1536x1024(가로), 1024x1536(세로)")
    parser.add_argument("--transparent", action="store_true", help="배경 투명")
    parser.add_argument("--ref", type=Path, action="append", default=[], help="참고하거나 고칠 이미지 (여러 번 가능)")
    parser.add_argument("--effort", default="low", choices=["minimal", "low", "medium", "high"],
                        help="Codex가 프롬프트를 다듬는 생각 수준 (낮을수록 빠름)")
    args = parser.parse_args()

    if args.size and not re.fullmatch(r"\d{3,4}x\d{3,4}", args.size):
        fail("--size 는 1536x1024 같은 형식이어야 합니다.")
    for ref in args.ref:
        if not ref.is_file():
            fail(f"참고 이미지를 찾을 수 없습니다: {ref}")

    check_codex()

    out = (args.out or default_out_path(args.prompt)).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    workdir = Path(tempfile.mkdtemp(prefix="gpt-bridge-"))
    generated_dir = codex_home / "generated_images"
    existing = list_images(generated_dir)

    cmd = [
        "codex", "exec",
        "--skip-git-repo-check", "--ephemeral",
        "-s", "workspace-write",
        "-C", str(workdir),
        "-c", f'model_reasoning_effort="{args.effort}"',
    ]
    for ref in args.ref:
        cmd += ["-i", str(ref.resolve())]
    cmd.append(build_prompt(args.prompt, args.size, args.transparent, bool(args.ref)))

    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT_SEC)
        log_text = proc.stdout + proc.stderr
        if proc.returncode != 0:
            fail(explain_failure(log_text), log_text)

        # 1) 지시대로 저장한 out.png → 2) 작업 폴더의 새 이미지 → 3) Codex 기본 저장 위치의 새 이미지
        img = workdir / "out.png"
        if not img.is_file():
            img = newest_new_image(workdir, set()) or newest_new_image(generated_dir, existing)
        if not img:
            fail("Codex가 끝났지만 그림 파일이 없습니다. " + explain_failure(log_text), log_text)

        if out.suffix.lower() != img.suffix.lower():
            out = out.with_suffix(img.suffix.lower())
        shutil.copyfile(img, out)
        print(out)
    except subprocess.TimeoutExpired:
        fail(f"{TIMEOUT_SEC // 60}분 안에 끝나지 않았습니다. 잠시 뒤에 다시 시도하세요.")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
