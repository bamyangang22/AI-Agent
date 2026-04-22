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
from my_agents.complaint_agent import complaint_agent


# ── Input Guardrail ───────────────────────────────────────

input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    Evaluate the user's message for a restaurant chatbot context.

    Set is_off_topic=true if the message is completely unrelated to restaurant services.
    Allowed topics: menu inquiries, food allergies, placing orders, table reservations,
    operating hours, complaints about food/service, and general restaurant-related questions.
    Small talk and greetings are always allowed.
    Off-topic examples: coding help, politics, math problems, unrelated personal questions.

    Set has_inappropriate_language=true if the message contains any of the following:
    - Profanity or swear words (욕설)
    - Hate speech or discriminatory language
    - Sexually explicit content
    - Threatening or violent language
    - Severe personal insults directed at staff

    Note: Expressing frustration or complaints about food/service is NOT inappropriate
    (e.g., "음식이 별로였어", "직원이 불친절했어" → allowed, route to Complaints Agent).

    Always provide a reason explaining your decision.
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

    final = result.final_output
    is_blocked = final.is_off_topic or final.has_inappropriate_language

    return GuardrailFunctionOutput(
        output_info=final,
        tripwire_triggered=is_blocked,
    )


# ── Triage Agent ──────────────────────────────────────────

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

    😤 COMPLAINTS AGENT - Route here for:
    - Dissatisfaction with food quality or taste
    - Poor service experience
    - Requests for refund or compensation
    - Any expression of disappointment or complaint
    - "별로였어", "불친절했어", "환불해줘", "너무 실망했어", "음식이 이상해"

    CLASSIFICATION PROCESS:
    1. Greet the customer by name warmly
    2. Listen carefully to their request
    3. If the intent is clear, route immediately with a friendly explanation
    4. If unclear, ask ONE clarifying question
    5. Always announce where you're routing them:
       - "메뉴 전문가에게 연결해 드릴게요! 🍽️"
       - "주문 담당자에게 연결해 드릴게요! 📋"
       - "예약 담당자에게 연결해 드릴게요! 📅"
       - "불만 처리 담당자에게 연결해 드릴게요! 😤"

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
        make_handoff(complaint_agent),
    ],
)