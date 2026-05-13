"""
교육 멀티 에이전트용 기본 Streamlit 채팅 UI.
실행: streamlit run streamlit_app.py
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from education_agent import build_multi_agent_app, initial_state

load_dotenv()

st.set_page_config(page_title="교육 멀티 에이전트", page_icon="📚", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph" not in st.session_state:
    st.session_state.graph = None


@st.cache_resource
def get_graph():
    return build_multi_agent_app()


def ensure_api_key() -> bool:
    if os.getenv("OPENAI_API_KEY"):
        return True
    st.error("`.env`에 `OPENAI_API_KEY`를 설정한 뒤 다시 실행하세요.")
    return False


st.title("교육 멀티 에이전트")
st.caption("Supervisor가 Quiz · Tutor · Researcher 중 하나로 라우팅합니다.")

if not ensure_api_key():
    st.stop()

if st.session_state.graph is None:
    st.session_state.graph = get_graph()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("meta"):
            with st.expander("실행 정보"):
                st.code(msg["meta"], language="text")

prompt = st.chat_input("학습 관련 질문을 입력하세요…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("에이전트 실행 중…"):
            state = initial_state(prompt)
            result = st.session_state.graph.invoke(state)
            answer = result.get("final_answer") or "(응답 없음)"
            route = result.get("route", "")
            search_preview = (result.get("search_results") or "")[:800]
            meta_lines = [
                f"route: {route}",
                f"search_results (앞 800자):\n{search_preview}" if route == "researcher" else "search_results: (해당 없음)",
            ]
            meta = "\n".join(meta_lines)
        st.markdown(answer)
        with st.expander("실행 정보"):
            st.code(meta, language="text")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "meta": meta}
    )
