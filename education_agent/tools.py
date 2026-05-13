"""교육 멀티 에이전트에서 Researcher가 사용하는 웹 검색 도구."""

from langchain_core.tools import tool
from duckduckgo_search import DDGS


@tool
def educational_web_lookup(query: str, max_results: int = 4) -> str:
    """교육·학습 질문 보조용 웹 검색. 최신 정보, 정의, 통계 확인에 사용합니다."""
    query = (query or "").strip()
    if not query:
        return "(검색어가 비어 있습니다.)"
    lines: list[str] = []
    try:
        with DDGS() as ddgs:
            found = list(ddgs.text(query, max_results=max_results))
        for i, item in enumerate(found, 1):
            title = item.get("title", "").strip()
            body = (item.get("body") or "").strip()[:400]
            href = item.get("href", "").strip()
            lines.append(f"{i}. {title}\n   {body}\n   {href}")
    except Exception as e:
        return f"(검색 중 오류: {e})"
    return "\n\n".join(lines) if lines else "(검색 결과 없음)"
