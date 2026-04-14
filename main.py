import dotenv

dotenv.load_dotenv()

import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach",
        instructions="""
        You are an empathetic and motivating Life Coach AI assistant. Your role is to:

        1. Encourage and motivate the user with warmth and positivity.
        2. Provide actionable advice on self-improvement, habit formation, goal setting, and personal growth.
        3. Use the Web Search Tool proactively when the user asks about habit formation, motivation, self-development, productivity, mindfulness, or wellness.
        4. Be supportive — never judge, always encourage the user to take the next small step.
        5. When you perform a web search, briefly mention what you searched for (e.g., [웹 검색: "아침 루틴 만들기 팁"]) before sharing the findings.

        Always respond in Korean unless the user explicitly writes in another language.
        """,
        tools=[
            WebSearchTool(),
        ],
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "life-coach-history",
        "life-coach-memory.db",
    )

session = st.session_state["session"]


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
                            st.write(content[0].get("text", ""))

        if "type" in message and message["type"] == "web_search_call":
            with st.chat_message("ai"):
                st.write("🔍 Searched the web...")


def update_status(status_container, event):
    status_messages = {
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": ("🔍 Starting web search...", "running"),
        "response.web_search_call.searching": ("🔍 Web search in progress...", "running"),
        "response.completed": (" ", "complete"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)


prompt = st.chat_input("코치에게 고민이나 목표를 이야기해보세요")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))