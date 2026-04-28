from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from .prompt import (
    ILLUSTRATOR_DESCRIPTION,
    ILLUSTRATOR_PROMPT,
    STORY_WRITER_DESCRIPTION,
    STORY_WRITER_PROMPT,
)
from .tools import generate_illustrations, write_story

MODEL = LiteLlm(model="openai/gpt-4o")

story_writer_agent = Agent(
    name="StoryWriterAgent",
    description=STORY_WRITER_DESCRIPTION,
    instruction=STORY_WRITER_PROMPT,
    model=MODEL,
    tools=[write_story],
)

illustrator_agent = Agent(
    name="IllustratorAgent",
    description=ILLUSTRATOR_DESCRIPTION,
    instruction=ILLUSTRATOR_PROMPT,
    model=MODEL,
    tools=[generate_illustrations],
)

root_agent = SequentialAgent(
    name="StorybookPipeline",
    description="Creates a children's storybook: writes a 5-page story then generates illustrations for each page.",
    sub_agents=[story_writer_agent, illustrator_agent],
)
