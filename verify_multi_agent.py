"""터미널에서 멀티 에이전트 end-to-end 스모크 테스트."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from education_agent import build_multi_agent_app, initial_state


def main() -> int:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 없습니다. .env를 확인하세요.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Education multi-agent smoke test")
    parser.add_argument(
        "question",
        nargs="?",
        default="2026년 대한민국 수능 일정을 웹 기준으로 요약해 줘",
        help="테스트할 학습자 질문",
    )
    args = parser.parse_args()

    app = build_multi_agent_app()
    out = app.invoke(initial_state(args.question))

    print("=== route ===")
    print(out.get("route"))
    print("=== final_answer (앞 500자) ===")
    text = out.get("final_answer") or ""
    print(text[:500] + ("…" if len(text) > 500 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
