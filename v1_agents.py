import os
# import sys
# sys.path.append(r"C:\Users\junej\OneDrive\Documents\bunq-hackathon-agents-6.0\category_mapping_Co2")
from typing import Dict
import asyncio
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic import BaseModel
from httpx import AsyncClient
from dataclasses import dataclass
from category_mapping_Co2 import CATEGORY_MAPPING, EMISSION_FACTORS_10
from dotenv import dotenv_values
from dotenv import load_dotenv
import pandas as pd

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
def calculate_co2_emissions(spending_by_raw_category: Dict[str, float]) -> Dict:
    mapped_spending = {}

    for raw_category, amount in spending_by_raw_category.items():
        broad_cat = CATEGORY_MAPPING.get(raw_category.strip().upper())
        if broad_cat:
            mapped_spending[broad_cat] = mapped_spending.get(broad_cat, 0) + amount

    co2_total = 0
    breakdown = {}

    for broad_cat, amount in mapped_spending.items():
        factor = EMISSION_FACTORS_10.get(broad_cat, 0)
        co2 = amount * factor
        breakdown[broad_cat] = {'spend': amount, 'co2': co2}
        co2_total += co2

    total_spend = sum(mapped_spending.values())
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
    user_df = df[df['counterparty_name'] == user_id]
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
        df = pd.read_csv(r"C:\Users\junej\OneDrive\Documents\bunq-hackathon-agents-6.0\transactions.csv")
        
        selected_user_id = "John Peter Clarkson"
        user_spending = get_user_spending(df, selected_user_id)
        print(user_spending)

        footprint_result = await base_agent.run(
            f"What is the carbon footprint for this user: {user_spending}", deps=deps
        )
        print("\n Carbon Footprint Response:\n", footprint_result.output)
        ##### END CO2 FOOTPRINT #####

if __name__ == '__main__':
    asyncio.run(main())
