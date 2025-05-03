from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio, MCPServerHTTP
from httpx import AsyncClient
import os
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dotenv import load_dotenv
import asyncio
from devtools import debug

load_dotenv()

bunq_server = MCPServerHTTP(url='http://localhost:8000/sse')
co2_server = MCPServerHTTP(url='http://localhost:8009/sse')


model = GeminiModel(
    'gemini-2.0-flash-exp', provider=GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
)

agent = Agent(model, mcp_servers=[bunq_server,co2_server])


async def main():
    async with agent.run_mcp_servers():
        result = await agent.run(
            'Hi gemini can you retrieve my transactions from my primary monetary bunq account and how do I improve my carbon footprint?'
        )
        debug(result)

        print('Response:', result.output)


if __name__ == '__main__':
    asyncio.run(main())