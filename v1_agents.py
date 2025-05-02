import os

import asyncio
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic import BaseModel
from httpx import AsyncClient
from dataclasses import dataclass

from dotenv import dotenv_values
from dotenv import load_dotenv

load_dotenv()  # take environment variables

config = dotenv_values(".env")


@dataclass
class Deps:
    client: AsyncClient
    bunq_api_key: str | None


model = GeminiModel('gemini-2.0-flash', provider='google-gla')

base_agent = Agent(
    model=model,
    system_prompt=(
        'Reply to whatever is asked clearly.',
        'First answer what the user has asked, then do below steps'
        'Use the `get_balance` tool to get balance of the user using bunq_api_key and return the balance with proper sentence',
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
)


@base_agent.tool
def get_balance(ctx: "RunContext[Deps]") -> float:
    if ctx.deps.bunq_api_key:
        return 100.0


async def main():
    async with AsyncClient() as client:
        bunq_api_key = config['BUNQ_API_KEY']

        deps = Deps(
            client=client, bunq_api_key=bunq_api_key
        )
        result = await base_agent.run(
            'What are my bank details?', deps=deps
        )
        # debug(result)
        print('Response:', result.output)


if __name__ == '__main__':
    asyncio.run(main())
