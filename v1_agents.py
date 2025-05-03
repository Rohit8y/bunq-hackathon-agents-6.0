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
from pydantic import BaseModel, Field
import pandas as pd

load_dotenv()  # take environment variables

config = dotenv_values(".env")


@dataclass
class Deps:
    client: AsyncClient
    bunq_api_key: str | None

class CalculateCO2(BaseModel):
    total_co2: float
    co2_per_euro: float 
    zone: str 

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

# Define the agent using LLM for category classification
base_agent_Co2_calc = Agent(
    model=model,
system_prompt = (
    "You are an intelligent financial sustainability agent. Your task is to analyze a user's spending and calculate their carbon footprint.",
    "1. First, classify each spending item into one of these 10 broad CO₂ categories:",
    "   - travel_transport",
    "   - food_dining",
    "   - groceries_household",
    "   - shopping_fashion",
    "   - housing_utilities",
    "   - entertainment_subscriptions",
    "   - health_wellness",
    "   - education_books",
    "   - financial_services",
    "   - charity_gifts",
    "2. Once classified, apply the following carbon intensity factors (in kg CO₂ per €):",
    "   - travel_transport: 0.8",
    "   - food_dining: 0.6",
    "   - groceries_household: 0.5",
    "   - shopping_fashion: 0.5",
    "   - housing_utilities: 0.3",
    "   - entertainment_subscriptions: 0.3",
    "   - health_wellness: 0.2",
    "   - education_books: 0.2",
    "   - financial_services: 0.1",
    "   - charity_gifts: 0.05",
    "3. Then compute:",
    "   - total CO₂ emissions (sum of all categories)",
    "   - average CO₂ per € spent",
    "   - a sustainability zone based on thresholds:",
    "     - Green: CO₂/€ < 0.4",
    "     - Yellow: 0.4 ≤ CO₂/€ ≤ 0.6",
    "     - Red: CO₂/€ > 0.6",
    "Only reply with JSON object containing only 3 fields: total_co2, co2_per_euro, zone.",
    "Do not respond with explanations, summaries, or markdown formatting outside this block.",
    "Politely refuse and redirect if the user asks for unethical or unrelated requests (e.g. how to emit more CO₂)."
),


    deps_type=Deps,
    retries=2,
    instrument=True,
    output_type=CalculateCO2

)

###### HELPER FUNCTIONS ######
def get_user_spending(df: pd.DataFrame, user_id: str) -> Dict[str, float]:
    """
    Aggregates spending by category for a specific user.
    """
    user_df = df[df['counterparty_name'] == user_id]
    return user_df.groupby('category')['amount'].sum().to_dict()
###### END HELPER FUNCTIONS #####

# # Tool 1: Get balance
@base_agent.tool
def get_balance(ctx: "RunContext[Deps]") -> float:
    if ctx.deps.bunq_api_key:
        return 100.0


# Tool 2: Calculate footprint
# @base_agent.tool
# def calculate_footprint(ctx: "RunContext[Deps]", spending: Dict[str, float]) -> Dict:
#     return calculate_co2_emissions(spending)



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

#         ##### CO2 FOOTPRINT #####
        df = pd.read_csv(r"C:\Users\junej\OneDrive\Documents\bunq-hackathon-agents-6.0\transactions.csv")
        df = df[:10]
        selected_user_id = "John Peter Clarkson"
        user_spending = get_user_spending(df, selected_user_id)
        print(f"\nRaw Spending for {selected_user_id}:\n", user_spending)

        # Let the LLM classify and calculate
        formatted_spending = ", ".join([f"{amount} euros on {cat}" for cat, amount in user_spending.items()])
        footprint_prompt = f"Calculate the carbon footprint for the following spending: {formatted_spending}"
        footprint_result = await base_agent_Co2_calc.run(footprint_prompt, deps=deps)
        print("\nCarbon Footprint Response:\n", footprint_result.output)
#         ##### END CO2 FOOTPRINT #####

if __name__ == '__main__':
    asyncio.run(main())



