import os

from dotenv import load_dotenv
from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


# Load variables from the .env file.
load_dotenv()


class LLMService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY was not found. "
                "Make sure the .env file is beside main.py."
            )

        self.client = OpenAIChatCompletionClient(
            model=model_name,
            api_key=api_key,
        )

    async def ask(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        result = await self.client.create(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(
                    content=user_prompt,
                    source="user",
                ),
            ]
        )

        return str(result.content)

    async def close(self) -> None:
        await self.client.close()