import os
import asyncio
import dotenv
import streamlit as st

from openai import OpenAI
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

# =========================================================
# 0. 환경 변수 로드
# =========================================================
dotenv.load_dotenv()

# OpenAI 클라이언트
client = OpenAI()

# =========================================================
# 1. 설정값
# =========================================================
# 실습용으로 하나의 Vector Store를 사용합니다.
# .env 등에 미리 저장한 VECTOR_STORE_ID를 사용해도 되고,
# 아래처럼 직접 문자열로 넣어도 됩니다.
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "YOUR_VECTOR_STORE_ID")

# 세션/메모리 파일명
SESSION_NAME = "life-coach-history"
SESSION_DB_PATH = "life-coach-memory.db"

# 페이지 기본 설정
st.set_page_config(
    page_title="Life Coach: File Search",
    page_icon="🧭",
    layout="centered",
)

st.title("🧭 Life Coach: File Search")
st.caption("목표 문서를 업로드하고, 코치에게 개인화된 조언을 받아보세요.")

# =========================================================
# 2. Agent 초기화
#    - Life Coach 역할
#    - Web Search Tool
#    - File Search Tool
# =========================================================
def build_agent() -> Agent:
    """
    Life Coach Agent 생성
    - 목표 / 일기 / 계획 / 진행상황 질문에서는 File Search를 우선 활용
    - 최신 팁 / 습관 / 생산성 / 웰빙 정보는 Web Search 활용
    """

    return Agent(
        name="Life Coach",
        instructions="""
You are an empathetic and motivating Life Coach AI assistant.

Your job:
1. Be warm, supportive, and practical.
2. Help the user with goals, journaling, progress checks, habits, motivation, and self-improvement.
3. If the user asks about their goals, plans, diary entries, routines, or progress, use the File Search Tool first to reference their uploaded documents.
4. If the user asks for current advice, recent research, or up-to-date tips, use the Web Search Tool.
5. When both are useful, combine:
   - the user's uploaded goal documents
   - recent web results
6. When you use file search, briefly reflect that you checked the user's uploaded goals or notes.
7. When you use web search, briefly mention what topic you searched for.
8. Give concrete next steps, not vague encouragement only.
9. Always respond in Korean unless the user explicitly uses another language.

Important behavior:
- If the uploaded documents do not clearly contain enough information, say so honestly.
- Do not pretend to know the user's progress if there is no evidence.
- For progress tracking questions, compare the user's stated goal with the current conversation or uploaded notes when possible.
- Keep answers clean and easy to follow.
""",
        tools=[
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],
                max_num_results=3,
            ),
            WebSearchTool(),
        ],
    )


# =========================================================
# 3. Streamlit session_state 초기화
#    - agent
#    - SQLiteSession
# =========================================================
if "agent" not in st.session_state:
    st.session_state["agent"] = build_agent()

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        SESSION_NAME,
        SESSION_DB_PATH,
    )

agent = st.session_state["agent"]
session = st.session_state["session"]

# =========================================================
# 4. UI 보조 함수
#    - 과거 대화 렌더링
#    - 상태 메시지 갱신
# =========================================================
async def paint_history():
    """
    저장된 대화 기록을 화면에 다시 그립니다.
    실습에서는 메시지 / 파일검색 / 웹검색 흔적이 보이도록 구성합니다.
    """
    messages = await session.get_items()

    for message in messages:
        # 일반 대화 메시지 출력
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    content = message.get("content", "")

                    # user content가 문자열인 경우
                    if isinstance(content, str):
                        st.write(content)

                    # 혹시 list 구조가 들어오더라도 안전하게 처리
                    elif isinstance(content, list):
                        for part in content:
                            if part.get("type") == "input_text":
                                st.write(part.get("text", ""))
                else:
                    # assistant 메시지 출력
                    if message.get("type") == "message":
                        content = message.get("content", [])
                        if content and isinstance(content, list):
                            text = content[0].get("text", "")
                            st.write(text.replace("$", r"\$"))

        # tool call 흔적 표시
        if "type" in message:
            if message["type"] == "file_search_call":
                with st.chat_message("assistant"):
                    st.write("🗂️ 목표/기록 문서를 검색했어요.")
            elif message["type"] == "web_search_call":
                with st.chat_message("assistant"):
                    st.write("🔍 웹에서 관련 정보를 검색했어요.")


def update_status(status_container, event_type: str):
    """
    스트리밍 중 발생하는 이벤트에 따라 상태 UI를 갱신합니다.
    사용자 입장에서 '지금 무엇을 하고 있는지'가 보이도록 작성했습니다.
    """
    status_messages = {
        # 파일 검색 상태
        "response.file_search_call.in_progress": ("🗂️ 목표 문서 검색 시작...", "running"),
        "response.file_search_call.searching": ("🗂️ 목표 문서 검색 중...", "running"),
        "response.file_search_call.completed": ("✅ 목표 문서 검색 완료", "complete"),

        # 웹 검색 상태
        "response.web_search_call.in_progress": ("🔍 웹 검색 시작...", "running"),
        "response.web_search_call.searching": ("🔍 웹 검색 중...", "running"),
        "response.web_search_call.completed": ("✅ 웹 검색 완료", "complete"),

        # 전체 응답 완료
        "response.completed": ("✅ 답변 완료", "complete"),
    }

    if event_type in status_messages:
        label, state = status_messages[event_type]
        status_container.update(label=label, state=state)


# 앱 시작 시 이전 대화 출력
asyncio.run(paint_history())

# =========================================================
# 5. 파일 업로드 처리 함수
#    - 목표 문서(txt/pdf) 업로드
#    - OpenAI files 업로드
#    - Vector Store 연결
# =========================================================
def upload_file_to_vector_store(uploaded_file) -> None:
    """
    사용자가 올린 목표 문서를 OpenAI Files에 업로드하고,
    File Search가 가능하도록 Vector Store에 연결합니다.
    """
    with st.chat_message("assistant"):
        with st.status("⏳ 목표 문서 업로드 중...", expanded=False) as status:
            # 1) OpenAI Files에 업로드
            uploaded = client.files.create(
                file=(uploaded_file.name, uploaded_file.getvalue()),
                purpose="user_data",
            )

            status.update(label="⏳ 벡터 스토어에 연결 중...", state="running")

            # 2) Vector Store에 연결
            client.vector_stores.files.create(
                vector_store_id=VECTOR_STORE_ID,
                file_id=uploaded.id,
            )

            status.update(
                label=f"✅ 업로드 완료: {uploaded_file.name}",
                state="complete",
            )


# =========================================================
# 6. Agent 실행 함수
#    - Runner.run_streamed()
#    - 응답 스트리밍
#    - file/web search 상태를 UI에 표시
# =========================================================
async def run_agent(user_message: str):
    """
    사용자 질문을 Agent에 전달하고,
    스트리밍 응답을 실시간으로 출력합니다.
    """
    with st.chat_message("assistant"):
        status_container = st.status("⏳ 코치가 생각 중입니다...", expanded=False)
        text_placeholder = st.empty()
        full_response = ""

        stream = Runner.run_streamed(
            agent,
            user_message,
            session=session,
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                raw_type = event.data.type

                # 1) 현재 진행 상태 업데이트
                update_status(status_container, raw_type)

                # 2) 텍스트 토큰이 들어오면 실시간으로 이어붙여 출력
                if raw_type == "response.output_text.delta":
                    full_response += event.data.delta
                    text_placeholder.write(full_response.replace("$", r"\$"))


# =========================================================
# 7. 사용자 입력 UI
#    - 텍스트 질문
#    - 목표 문서 업로드(txt, pdf)
# =========================================================
prompt = st.chat_input(
    "목표, 루틴, 진행상황을 코치에게 물어보세요. 목표 문서도 함께 업로드할 수 있어요.",
    accept_file=True,
    file_type=["txt", "pdf"],
)

if prompt:
    # -----------------------------------------------------
    # 사용자 흐름 A. 파일 먼저 업로드
    # -----------------------------------------------------
    # 사용자가 목표 문서(txt/pdf)를 첨부하면
    # 1) 파일 업로드
    # 2) vector store 연결
    # 3) 이후 agent가 해당 문서를 검색해서 답변 가능
    # -----------------------------------------------------
    for uploaded_file in prompt.files:
        upload_file_to_vector_store(uploaded_file)

    # -----------------------------------------------------
    # 사용자 흐름 B. 텍스트 질문 처리
    # -----------------------------------------------------
    # 사용자가 질문을 입력하면
    # 1) 화면에 사용자 메시지 표시
    # 2) agent 실행
    # 3) 필요 시 file search / web search 수행
    # 4) 스트리밍 응답 출력
    # -----------------------------------------------------
    if prompt.text:
        with st.chat_message("user"):
            st.write(prompt.text)

        asyncio.run(run_agent(prompt.text))

# =========================================================
# 8. 사이드바
#    - 사용 가이드
#    - 메모리 초기화
#    - 디버깅용 세션 보기
# =========================================================
with st.sidebar:
    st.subheader("사용 방법")
    st.markdown(
        """
1. 목표 문서(txt/pdf)를 업로드합니다.  
2. 예:  
   - 내 운동 목표 잘 진행 중이야?  
   - 내 공부 루틴에 맞는 조언 해줘  
   - 지난 기록 기준으로 뭐를 보완하면 좋을까?  
3. 코치는 업로드 문서를 먼저 참고하고, 필요하면 웹 검색도 함께 사용합니다.
"""
    )

    st.divider()

    if st.button("Reset memory"):
        asyncio.run(session.clear_session())
        st.success("대화 메모리를 초기화했습니다.")
        st.rerun()

    st.divider()

    show_debug = st.checkbox("세션 데이터 보기")
    if show_debug:
        st.write(asyncio.run(session.get_items()))