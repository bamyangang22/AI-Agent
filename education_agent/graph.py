"""
Option A: 멀티 에이전트 (Supervisor → Quiz | Tutor | Researcher)
LangGraph StateGraph로 감독자가 의도를 분류하고 전문 서브 에이전트가 답변을 생성합니다.
"""

from __future__ import annotations

import json
import re
from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from education_agent.tools import educational_web_lookup

Route = Literal["quiz", "tutor", "researcher"]


class EducationMultiAgentState(TypedDict):
    user_question: str
    route: str
    search_results: str
    final_answer: str


def _extract_json_object(raw: str) -> str:
    raw = raw.strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    return m.group(0) if m else raw


def _parse_supervisor_json(raw: str) -> Route:
    data = json.loads(_extract_json_object(raw))
    r = (data.get("route") or "").strip().lower()
    if r in ("quiz", "tutor", "researcher"):
        return r  # type: ignore[return-value]
    return "tutor"


def supervisor_node(state: EducationMultiAgentState, llm: ChatOpenAI) -> EducationMultiAgentState:
    q = state["user_question"]
    messages = [
        SystemMessage(
            content="""당신은 교육 멀티 에이전트 시스템의 Supervisor(감독자)입니다.
학습자의 한국어 질문을 보고 **정확히 하나**의 전문 에이전트로 라우팅하세요.

- quiz: 퀴즈·문제 출제, 객관식/주관식 연습, 시험 대비 문제를 원할 때
- tutor: 개념 설명, 학습 순서, 코드/수학 아이디어 설명, 이해를 돕는 조언
- researcher: 최신 일정·정책·뉴스, 통계·수치, 사실 확인이 필요한 조회형 질문

반드시 JSON 한 덩어리만 출력하세요. 키: route (문자열, "quiz" | "tutor" | "researcher" 중 하나)."""
        ),
        HumanMessage(content=q),
    ]
    raw = llm.invoke(messages).content.strip()
    try:
        route = _parse_supervisor_json(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        route = "tutor"
    state["route"] = route
    return state


def quiz_node(state: EducationMultiAgentState, llm: ChatOpenAI) -> EducationMultiAgentState:
    q = state["user_question"]
    messages = [
        SystemMessage(
            content="""당신은 Quiz 전문 에이전트입니다. 한국어로 응답하세요.
학습자 요청에 맞춰 연습용 퀴즈를 만드세요. 가능하면 객관식 3~5문항(보기 포함)과 정답·간단 해설을 제시하세요.
마크다운으로 읽기 좋게 구조화하세요."""
        ),
        HumanMessage(content=q),
    ]
    state["final_answer"] = llm.invoke(messages).content
    return state


def tutor_node(state: EducationMultiAgentState, llm: ChatOpenAI) -> EducationMultiAgentState:
    q = state["user_question"]
    messages = [
        SystemMessage(
            content="""당신은 Tutor 전문 에이전트입니다. 한국어로 응답하세요.
개념을 단계적으로 설명하고, 필요하면 예시·비유·학습 팁을 덧붙이세요.
마크다운으로 읽기 좋게 구조화하세요."""
        ),
        HumanMessage(content=q),
    ]
    state["final_answer"] = llm.invoke(messages).content
    return state


def _researcher_search_query(llm: ChatOpenAI, user_question: str) -> str:
    messages = [
        SystemMessage(
            content="""웹 검색용 짧은 검색어 한 줄을 한국어 또는 영어로만 출력하세요.
질문의 핵심 키워드만 담고, 설명·따옴표·JSON은 금지입니다."""
        ),
        HumanMessage(content=user_question),
    ]
    return (llm.invoke(messages).content or "").strip().split("\n")[0].strip()[:200] or user_question[:200]


def researcher_node(state: EducationMultiAgentState, llm: ChatOpenAI) -> EducationMultiAgentState:
    q = state["user_question"]
    sq = _researcher_search_query(llm, q)
    tool_out = educational_web_lookup.invoke({"query": sq, "max_results": 4})
    ctx = tool_out if isinstance(tool_out, str) else str(tool_out)
    state["search_results"] = ctx
    messages = [
        SystemMessage(
            content="""당신은 Researcher 전문 에이전트입니다. 한국어로 응답하세요.
아래 웹 검색 요약을 참고해 질문에 답하세요. 출처가 불명확하면 단정하지 마세요.
마크다운으로 읽기 좋게 구조화하세요."""
        ),
        HumanMessage(
            content=f"질문:\n{q}\n\n검색어: {sq}\n\n웹 검색 요약:\n{ctx}\n\n위를 바탕으로 답해 주세요."
        ),
    ]
    state["final_answer"] = llm.invoke(messages).content
    return state


def _route_after_supervisor(state: EducationMultiAgentState) -> Route:
    r = (state.get("route") or "tutor").strip().lower()
    if r in ("quiz", "tutor", "researcher"):
        return r  # type: ignore[return-value]
    return "tutor"


def build_multi_agent_app(llm: ChatOpenAI | None = None):
    """Supervisor → (quiz | tutor | researcher) → END 그래프를 컴파일합니다."""
    model = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    def _sup(s: EducationMultiAgentState) -> EducationMultiAgentState:
        return supervisor_node(s, model)

    def _qz(s: EducationMultiAgentState) -> EducationMultiAgentState:
        return quiz_node(s, model)

    def _tu(s: EducationMultiAgentState) -> EducationMultiAgentState:
        return tutor_node(s, model)

    def _rs(s: EducationMultiAgentState) -> EducationMultiAgentState:
        return researcher_node(s, model)

    g = StateGraph(EducationMultiAgentState)
    g.add_node("supervisor", _sup)
    g.add_node("quiz", _qz)
    g.add_node("tutor", _tu)
    g.add_node("researcher", _rs)
    g.set_entry_point("supervisor")
    g.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {"quiz": "quiz", "tutor": "tutor", "researcher": "researcher"},
    )
    g.add_edge("quiz", END)
    g.add_edge("tutor", END)
    g.add_edge("researcher", END)
    return g.compile()


def initial_state(user_question: str) -> EducationMultiAgentState:
    return {
        "user_question": user_question.strip(),
        "route": "",
        "search_results": "",
        "final_answer": "",
    }
