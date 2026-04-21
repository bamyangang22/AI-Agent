from agents import Agent, RunContextWrapper
from models import RestaurantContext
from tools import place_order, confirm_order, cancel_order


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    table_info = f"테이블 {wrapper.context.table_number}번" if wrapper.context.table_number else "테이블 미지정"
    party_info = f"{wrapper.context.party_size}명" if wrapper.context.party_size else "인원 미확인"

    return f"""
    You are a friendly Order Specialist at our restaurant, assisting {wrapper.context.customer_name}.
    Always respond in Korean.

    CURRENT SESSION INFO:
    - Customer: {wrapper.context.customer_name}
    - {table_info}
    - Party size: {party_info}

    YOUR ROLE: Take, confirm, and manage customer orders accurately.

    ORDER PROCESS:
    1. Confirm their table number if not set
    2. Take their order item by item, confirming each one
    3. Ask about any special requests or dietary modifications
    4. Summarize the full order and ask for confirmation
    5. Place the order using the place_order tool

    TONE: Efficient, friendly, and attentive 📋
    """


order_agent = Agent(
    name="Order Agent",
    instructions=dynamic_order_agent_instructions,
    tools=[
        place_order,
        confirm_order,
        cancel_order,
    ],
)