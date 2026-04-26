import os
import asyncio
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from agents import (
    Runner,
    SQLiteSession,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from models import RestaurantContext
from my_agents.triage_agent import triage_agent

_dotenv_path = find_dotenv(usecwd=True)
load_dotenv(_dotenv_path)

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

client = OpenAI(api_key=_api_key)

st.set_page_config(page_title="🍽️ Restaurant Bot", page_icon="🍽️", layout="wide")
st.title("🍽️ Restaurant Bot")
st.caption("메뉴 문의, 주문, 예약을 도와드립니다!")

restaurant_ctx = RestaurantContext(
    customer_name="지수",
    table_number=5,
    party_size=2,
)

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "restaurant-chat",
        "restaurant-bot-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

with st.sidebar:
    st.markdown("## 👤 고객 정보")
    st.write(f"**이름:** {restaurant_ctx.customer_name}")
    st.write(f"**테이블:** {restaurant_ctx.table_number}번")
    st.write(f"**인원:** {restaurant_ctx.party_size}명")
    st.markdown("---")
    st.markdown("## 🤖 현재 에이전트")
    agent_placeholder = st.empty()
    agent_placeholder.write(f"`{st.session_state['agent'].name}`") 
    st.markdown("---")
    if st.button("🗑️ 대화 초기화"):
        asyncio.run(session.clear_session())
        st.session_state["agent"] = triage_agent
        st.rerun()
    st.markdown("### 📜 대화 기록")
    st.write(asyncio.run(session.get_items()))

async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message.get("type") == "message":
                        content = message.get("content", [])
                        if content and isinstance(content, list):
                            st.write(content[0]["text"].replace("$", "\\$"))


asyncio.run(paint_history())


async def run_agent(message: str, agent_placeholder):
    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""
        st.session_state["text_placeholder"] = text_placeholder

        try:
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=restaurant_ctx,
            )

            # OutputGuardrailTripwireTriggered는 stream_events() 내부에서
            # 발생하므로 루프 안에서도 잡을 수 있도록 전체를 try로 감쌈
            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\\$"))

                elif event.type == "agent_updated_stream_event":
                    if st.session_state["agent"].name != event.new_agent.name:
                        old_agent_name = st.session_state["agent"].name
                        st.session_state["agent"] = event.new_agent
                        agent_placeholder.write(f"`{event.new_agent.name}`")
                        text_placeholder.info(f"🔀 **{old_agent_name}** → **{event.new_agent.name}** 으로 연결합니다...")  
                        text_placeholder = st.empty()
                        response = ""

        except InputGuardrailTripwireTriggered as e:
            # warning() 대신 write()로 일반 채팅 말풍선 안에 표시
            guardrail_output = e.guardrail_result.output.output_info
            if guardrail_output.has_inappropriate_language:
                text_placeholder.write(
                    "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. "
                    "정중한 표현으로 메뉴, 주문, 예약, 불만 사항에 대해 물어봐 주세요. 😊"
                )
            else:
                text_placeholder.write(
                    "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. "
                    "메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요."
                )

        except OutputGuardrailTripwireTriggered as e:
            # safe_response가 있으면 사용, 없으면 기본 안내 메시지
            guardrail_output = e.guardrail_result.output.output_info
            safe_msg = (
                guardrail_output.safe_response
                if guardrail_output.safe_response
                else (
                    "죄송합니다. 보다 적절한 방식으로 도움을 드리겠습니다. "
                    "불편하신 점을 다시 말씀해 주시겠어요? 🙏"
                )
            )
            text_placeholder.write(safe_msg)


message = st.chat_input("무엇을 도와드릴까요? (예: 메뉴 알려줘 / 주문할게요 / 예약하고 싶어 / 불만 있어요)")

if message:
    with st.chat_message("human"):
        st.write(message)
    asyncio.run(run_agent(message, agent_placeholder))