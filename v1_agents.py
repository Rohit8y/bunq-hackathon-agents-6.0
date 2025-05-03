import os
from typing import Dict
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
        'If the user asks for carbon footprint based on spending, use the `calculate_footprint` tool.',
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
)

###### HELPER FUNCTIONS ######
def calculate_co2_emissions(spending: Dict[str, float]) -> Dict:
    EMISSION_FACTORS = {
        'travel': 0.8,
        'food': 0.6,
        'shopping': 0.5,
        'housing': 0.3,
        'entertainment': 0.3,
    }

    co2_total = 0
    breakdown = {}
    for category, amount in spending.items():
        factor = EMISSION_FACTORS.get(category, 0)
        co2 = amount * factor
        breakdown[category] = {'spend': amount, 'co2': co2}
        co2_total += co2

    total_spend = sum(spending.values())
    co2_per_euro = co2_total / total_spend if total_spend else 0

    if co2_per_euro < 0.4:
        zone = 'Green'
    elif 0.4 <= co2_per_euro <= 0.6:
        zone = 'Yellow'
    else:
        zone = 'Red'

    return {
        'total_spend': total_spend,
        'total_co2': co2_total,
        'co2_per_euro': round(co2_per_euro, 3),
        'zone': zone,
        'breakdown': breakdown
    }

def get_user_spending(df: pd.DataFrame, user_id: str) -> Dict[str, float]:
    """
    Aggregates spending by category for a specific user.
    """
    user_df = df[df['user_id'] == user_id]
    return user_df.groupby('category')['amount'].sum().to_dict()
###### END HELPER FUNCTIONS #####

# Tool 1: Get balance
@base_agent.tool
def get_balance(ctx: "RunContext[Deps]") -> float:
    if ctx.deps.bunq_api_key:
        return 100.0


# Tool 2: Calculate footprint
@base_agent.tool
def calculate_footprint(ctx: "RunContext[Deps]", spending: Dict[str, float]) -> Dict:
    return calculate_co2_emissions(spending)



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

        ##### CO2 FOOTPRINT #####
        df = pd.DataFrame(data)
        selected_user_id = "placeholder"
        user_spending = get_user_spending(df, selected_user_id)

        footprint_result = await base_agent.run(
            f"What is the carbon footprint for this user: {user_spending}", deps=deps
        )
            print("\n Carbon Footprint Response:\n", footprint_result.output)
        ##### END CO2 FOOTPRINT #####

if __name__ == '__main__':
    asyncio.run(main())
