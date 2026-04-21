import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import RestaurantContext, InputGuardRailOutput, HandoffData
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    Determine if the user's request is related to a restaurant context.
    Allowed topics: menu inquiries, food allergies, placing orders, table reservations, operating hours, and general restaurant-related questions.
    Small talk and greetings are allowed.
    If the request is completely off-topic (e.g., coding help, politics, unrelated tasks), set is_off_topic to true and provide a reason.
""",
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    You are a warm and welcoming host at our restaurant, assisting {wrapper.context.customer_name}.
    Always respond in Korean.

    YOUR MAIN JOB: Understand what the customer needs and route them to the right specialist.

    ROUTING GUIDE:

    🍽️ MENU AGENT - Route here for:
    - Questions about today's menu or specific dishes
    - Ingredient or allergen inquiries
    - Vegetarian, vegan, or dietary option questions
    - Dish recommendations
    - "메뉴 알려줘", "채식 메뉴 있어?", "이 요리 뭐가 들어가?"

    📋 ORDER AGENT - Route here for:
    - Placing a new food or drink order
    - Modifying or canceling an existing order
    - Checking order status
    - "주문할게요", "~로 주문해줘", "주문 취소하고 싶어"

    📅 RESERVATION AGENT - Route here for:
    - Making a table reservation
    - Checking reservation availability
    - Canceling or modifying a reservation
    - "예약하고 싶어", "자리 있어?", "예약 취소해줘"

    CLASSIFICATION PROCESS:
    1. Greet the customer by name warmly
    2. Listen carefully to their request
    3. If the intent is clear, route immediately with a friendly explanation
    4. If unclear, ask ONE clarifying question
    5. Always say where you're routing them: "메뉴 전문가에게 연결해 드릴게요! 🍽️"

    TONE: Warm, cheerful, and hospitality-focused 🏡
    """


def handle_handoff(
    wrapper: RunContextWrapper[RestaurantContext],
    input_data: HandoffData,
):
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔀 Handoff 발생")
        st.write(f"**전달 대상:** {input_data.to_agent_name}")
        st.write(f"**이유:** {input_data.reason}")
        st.write(f"**유형:** {input_data.issue_type}")
        st.write(f"**설명:** {input_data.issue_description}")


def make_handoff(agent):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)