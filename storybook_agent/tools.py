import base64
import json

from google.adk.tools.tool_context import ToolContext
from google.genai import types
from openai import OpenAI

client = OpenAI()


async def write_story(theme: str, tool_context: ToolContext):
    """Generate a 5-page children's story and save it to state."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 어린이 동화 작가입니다. "
                    "모든 텍스트(text, visual_description)는 반드시 한국어로 작성하세요. "
                    "항상 유효한 JSON만 응답하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"다음 테마로 5페이지 분량의 어린이 동화를 한국어로 작성해주세요: {theme}\n\n"
                    "아래 구조의 JSON 객체로 반환하세요:\n"
                    '{"pages": [\n'
                    '  {"page_number": 1, "text": "동화 본문 (한국어)", "visual_description": "삽화 설명 (한국어)"},\n'
                    "  ...\n"
                    "]}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    story_data = json.loads(response.choices[0].message.content)
    pages = story_data.get("pages", [])

    tool_context.state["story_pages"] = pages

    return {
        "status": "success",
        "pages_written": len(pages),
        "pages": pages,
    }


async def generate_illustrations(tool_context: ToolContext):
    """Read story_pages from state and generate one image per page."""

    story_pages = tool_context.state.get("story_pages", [])

    if not story_pages:
        return {"status": "error", "message": "No story pages found in state"}

    existing_artifacts = await tool_context.list_artifacts()
    generated_images = []

    for page in story_pages:
        page_number = page.get("page_number")
        visual_description = page.get("visual_description")
        filename = f"page_{page_number}_image.jpeg"

        if filename in existing_artifacts:
            generated_images.append(
                {
                    "page_number": page_number,
                    "filename": filename,
                    "status": "already_exists",
                }
            )
            continue

        image = client.images.generate(
            model="gpt-image-1",
            prompt=f"Children's book illustration, soft watercolor style: {visual_description}",
            n=1,
            quality="low",
            moderation="low",
            output_format="jpeg",
            background="opaque",
            size="1024x1024",
        )

        image_bytes = base64.b64decode(image.data[0].b64_json)

        artifact = types.Part(
            inline_data=types.Blob(
                mime_type="image/jpeg",
                data=image_bytes,
            )
        )

        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact,
        )

        generated_images.append(
            {
                "page_number": page_number,
                "text": page.get("text"),
                "visual_description": visual_description,
                "filename": filename,
                "status": "generated",
            }
        )

    return {
        "total_images": len(generated_images),
        "generated_images": generated_images,
        "status": "complete",
    }
