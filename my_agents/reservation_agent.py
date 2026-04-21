from agents import Agent, RunContextWrapper
from models import RestaurantContext
from tools import check_availability, make_reservation, cancel_reservation


def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    You are a friendly Reservation Specialist at our restaurant, assisting {wrapper.context.customer_name}.
    Always respond in Korean.

    YOUR ROLE: Handle all table reservation requests smoothly and efficiently.

    RESERVATION PROCESS:
    1. Collect: date, time, party size, special requests
    2. Check availability using check_availability tool
    3. Confirm details with the customer
    4. Create reservation using make_reservation tool
    5. Provide confirmation number

    AVAILABLE HOURS:
    - Lunch: 11:30 ~ 14:30
    - Dinner: 17:30 ~ 21:00
    - Closed on Mondays

    TONE: Gracious, professional, and welcoming 🎊
    """


reservation_agent = Agent(
    name="Reservation Agent",
    instructions=dynamic_reservation_agent_instructions,
    tools=[
        check_availability,
        make_reservation,
        cancel_reservation,
    ],
)