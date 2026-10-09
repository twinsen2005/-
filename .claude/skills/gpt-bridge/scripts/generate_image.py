#!/usr/bin/env python3
"""GPT bridge: OpenAI 이미지 API로 그림을 만들어 PNG 파일로 저장한다.

표준 라이브러리만 사용하므로 별도 설치가 필요 없다.

사용 예:
    python3 generate_image.py "광합성 과정을 보여주는 단순한 교과서 삽화" --out images/photosynthesis.png
    python3 generate_image.py "물의 순환 모식도" --size 1536x1024 --quality high -n 2

환경 변수:
    OPENAI_API_KEY      (필수) OpenAI API 키
    OPENAI_IMAGE_MODEL  (선택) 기본값 gpt-image-1
    OPENAI_BASE_URL     (선택) 기본값 https://api.openai.com/v1
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "gpt-image-1"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
SIZES = ["auto", "1024x1024", "1536x1024", "1024x1536"]
QUALITIES = ["auto", "low", "medium", "high"]


def fail(message):
    print(f"[gpt-bridge] 오류: {message}", file=sys.stderr)
    sys.exit(1)


def default_out_path(prompt):
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", prompt).strip("_")[:30] or "image"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("images") / f"{stamp}_{slug}.png"


def numbered_paths(out, n):
    if n == 1:
        return [out]
    return [out.with_name(f"{out.stem}_{i}{out.suffix}") for i in range(1, n + 1)]


def request_images(args, api_key):
    base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
    }
    if args.transparent:
        payload["background"] = "transparent"

    req = urllib.request.Request(
        f"{base_url}/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(body)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            detail = body[:500]
        if e.code == 401:
            fail(f"API 키가 올바르지 않습니다 (401). {detail}")
        if e.code == 400 and "safety" in detail.lower():
            fail(f"안전 정책에 걸려 생성이 거부되었습니다. 프롬프트를 바꿔 보세요. {detail}")
        fail(f"OpenAI API 오류 {e.code}: {detail}")
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "403" in reason or "Tunnel" in reason:
            fail(
                "네트워크 정책이 api.openai.com 접속을 막았습니다. "
                "환경 설정 > Network access 의 Allowed domains 에 api.openai.com 을 추가하세요."
            )
        fail(f"네트워크 오류: {reason}")


def main():
    parser = argparse.ArgumentParser(description="OpenAI 이미지 API로 그림 생성")
    parser.add_argument("prompt", help="그림 설명 (영어가 보통 더 정확합니다)")
    parser.add_argument("--out", type=Path, help="저장할 PNG 경로 (기본: images/날짜_프롬프트.png)")
    parser.add_argument("--size", choices=SIZES, default="1024x1024")
    parser.add_argument("--quality", choices=QUALITIES, default="medium")
    parser.add_argument("-n", type=int, default=1, help="생성할 장수 (1~4)")
    parser.add_argument("--transparent", action="store_true", help="배경 투명 PNG")
    parser.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    if not 1 <= args.n <= 4:
        fail("-n 은 1~4 사이여야 합니다.")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        fail(
            "OPENAI_API_KEY 환경 변수가 없습니다. "
            "환경 설정에서 API 키를 등록한 뒤 새 세션에서 다시 실행하세요."
        )

    result = request_images(args, api_key)
    items = result.get("data") or []
    if not items:
        fail(f"응답에 이미지가 없습니다: {json.dumps(result)[:500]}")

    out = args.out or default_out_path(args.prompt)
    out.parent.mkdir(parents=True, exist_ok=True)
    for item, path in zip(items, numbered_paths(out, len(items))):
        if "b64_json" in item:
            path.write_bytes(base64.b64decode(item["b64_json"]))
        elif "url" in item:
            with urllib.request.urlopen(item["url"], timeout=120) as resp:
                path.write_bytes(resp.read())
        else:
            fail("응답 형식을 알 수 없습니다.")
        print(path)


if __name__ == "__main__":
    main()
