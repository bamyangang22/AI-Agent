from agents import Agent, RunContextWrapper
from models import RestaurantContext
from tools import get_menu, check_allergens, get_vegetarian_options


def dynamic_menu_agent_instructions(
    wrapper: RunContextWrapper[RestaurantContext],
    agent: Agent[RestaurantContext],
):
    return f"""
    You are a friendly Menu Specialist at our restaurant, assisting {wrapper.context.customer_name}.
    Always respond in Korean.

    YOUR ROLE: Answer all questions related to our menu, ingredients, and dietary needs.

    WHAT YOU CAN HELP WITH:
    - Explaining today's menu items in detail
    - Checking allergen and ingredient information
    - Recommending vegetarian or vegan options
    - Suggesting popular dishes or chef's specials

    TONE: Friendly, knowledgeable, and passionate about food 🍽️
    """


menu_agent = Agent(
    name="Menu Agent",
    instructions=dynamic_menu_agent_instructions,
    tools=[
        get_menu,
        check_allergens,
        get_vegetarian_options,
    ],
)