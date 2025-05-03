import asyncio
import os

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from dataclasses import dataclass
from dotenv import load_dotenv
import datetime
import random
from httpx import AsyncClient
from pydantic import BaseModel, Field
from typing import Dict, List
import pandas as pd
from src.utils.wrapper import Bunq_SDK_Wrapper

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

bunq_wrapper = Bunq_SDK_Wrapper()


class CalculateCO2(BaseModel):
    total_co2: float
    co2_per_euro: float
    zone: str


###### HELPER FUNCTIONS ######
def get_user_spending(df: pd.DataFrame, user_id: str) -> Dict[str, float]:
    """
    Aggregates spending by category for a specific user.
    """
    user_df = df[df['counterparty_name'] == user_id]
    return user_df.groupby('category')['amount'].sum().to_dict()


###### END HELPER FUNCTIONS #####

class CategoryPercentagePair(BaseModel):
    """Represents a single spending category and its percentage."""
    category: str = Field(description="The name of the spending category.")
    percentage: float = Field(description="The percentage of total spending for this category.")


class SpendingAnalysisOutput(BaseModel):
    """Represents the analysis of spending habits."""
    spending_summary_text: str = Field(
        description="A concise textual analysis of spending patterns, highlighting income sources (if any), major spending areas, and potential areas for saving."
    )
    category_percentage_distribution: List[CategoryPercentagePair] = Field(
        description="A list of spending categories and the percentage of total spending allocated to each. Excludes Income. Percentages should sum close to 100."
    )


@dataclass
class Deps:
    client: AsyncClient
    bunq_api_key: str | None


model = GeminiModel('gemini-2.0-flash', provider='google-gla')

bunq_agent = Agent(
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

# Define the agent using LLM for category classification
base_agent_Co2_calc = Agent(
    model=model,
    system_prompt=(
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

get_user_habits_agent = Agent(
    model=model,
    system_prompt=(
        "You are a financial analyst AI. When asked to analyze spending habits:\n"
        "1. Use the `get_fake_transactions` tool to retrieve transactions.\n"
        "2. Categorize transactions into: 'Groceries', 'Fuel', 'Travel', 'Subscriptions' and 'Other' categories using the descriptions in the transactions. Use 'Income' if amount is positive.\n"
        "3. Calculate total spending (sum of absolute negative amounts) and each spending category's percentage of this total.\n"
        "4. Generate `spending_summary_text`: concise analysis covering income sources, top 2-3 spending categories, and savings potential.\n"
        "5. Generate `category_percentage_distribution`: a **list** of objects, each with 'category' (string) and 'percentage' (float) for spending categories (must sum near 100%).\n"
        "6. Respond *strictly* using the `SpendingAnalysisOutput` format containing both fields. Politely refuse non-financial requests."
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
    output_type=SpendingAnalysisOutput

)

motivation_agent = Agent(
    model=model,
    system_prompt=(
        "You are a friendly climate coach. When told how much CO2 was offset, "
        "respond with a short and motivating message including a relatable comparison: "
        "e.g., trees planted, km cycled, or flights avoided. Keep it positive and inspiring!"
    ),
    deps_type=Deps,
    retries=2
)


@get_user_habits_agent.tool
async def get_fake_transactions(
        ctx: RunContext[Deps],
        num_transactions: int = 100,
        days_past: int = 10
):
    """
    Generates a list of fake transaction dictionaries and returns them
    within a dictionary under the key 'transactions'.
    """
    transactions_list = []
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_past)
    currencies = ["USD", "EUR", "GBP"]

    expense_descriptions = ['travel_transport',
                            'food_dining',
                            'groceries_household',
                            'shopping_fashion',
                            'housing_utilities',
                            'entertainment_subscriptions',
                            'health_wellness',
                            'education_books',
                            'financial_services',
                            'charity_gifts']

    credit_descriptions = ["salary", "gifts"]
    for i in range(num_transactions):
        random_date = start_date + datetime.timedelta(days=random.randint(0, days_past))
        is_credit = random.random() < 0.15

        if is_credit:

            amount = round(random.uniform(50.0, 2000.0), 2)
            description = random.choice(credit_descriptions)
        else:

            amount = round(random.uniform(-250.0, -1.0), 2)
            description = random.choice(expense_descriptions)

        transaction = {
            "id": f"txn_{random.randint(10000, 99999)}_{i}",
            "date": random_date.strftime("%Y-%m-%d"),
            "description": description,
            "amount": amount,
            "currency": random.choice(currencies)
        }

        transactions_list.append(transaction)

    return {"transactions": transactions_list}


@dataclass
class BunqData(BaseModel):
    green_account_balance: float


bunq_agent = Agent(
    model=model,
    system_prompt=(
        'First use `create_carbon_offset_account` tool to create a green account if it does not exist',
        'Then use `transfer_money_to_green_account` to transfer amount from main account to the green account',
        'Then use `get_balance_green_account` tool to return the user the green_account_balance',
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
    output_type=BunqData,
)


@bunq_agent.tool
def create_carbon_offset_account(ctx: "RunContext[Deps]"):
    if ctx.deps.bunq_api_key:
        green_account = bunq_wrapper.get_green_account()
        if not green_account:
            print("Creating account")
            bunq_wrapper.create_monetary_account(description="Green")
        else:
            print("Account already exists")


@bunq_agent.tool
def transfer_money_to_green_account(ctx: "RunContext[Deps]", amount):
    if ctx.deps.bunq_api_key:
        green_account = bunq_wrapper.get_green_account()
        main_account = bunq_wrapper.get_main_account()
        bunq_wrapper.transfer_between_accounts(main_account.id_, green_account.id_, amount, description="Carbon offset transfer")


@bunq_agent.tool
def get_balance_green_account(ctx: "RunContext[Deps]") -> float:
    if ctx.deps.bunq_api_key:
        balance = bunq_wrapper.get_green_account().balance
        print(balance)
        return balance.value


async def main():
    async with AsyncClient() as client:
        bunq_api_key = os.environ.get('BUNQ_API_KEY')

        deps = Deps(
            client=client, bunq_api_key=bunq_api_key
        )
        response = await get_user_habits_agent.run(
            "Can you analyze my recent spending patterns and tell me where my money is going?",
            deps=deps
        )
        print("\n--- User Habits Agent Analysis Result ---")
        print("\nSpending Summary Text:")
        print(response.output.spending_summary_text)
        print("\nCategory Percentage Distribution:")
        print(response.output.category_percentage_distribution)

        #         ##### CO2 FOOTPRINT #####
        df = pd.read_csv(r"../data/transactions.csv")
        df = df[:10]
        selected_user_id = "John Peter Clarkson"
        user_spending = get_user_spending(df, selected_user_id)
        raw_amount = user_spending.get("TRANSFER", 0)
        print(raw_amount)
        print(f"\nRaw Spending for {selected_user_id}:\n", user_spending)

        # Let the LLM classify and calculate
        formatted_spending = ", ".join([f"{amount} euros on {cat}" for cat, amount in user_spending.items()])
        footprint_prompt = f"Calculate the carbon footprint for the following spending: {formatted_spending}"
        footprint_result = await base_agent_Co2_calc.run(footprint_prompt, deps=deps)
        print("\nCarbon Footprint Response:\n", footprint_result.output)
        offset_amount = footprint_result.output.total_co2
        #         ##### END CO2 FOOTPRINT #####
        bunq_prompt = f"Transfer the offset_amount {offset_amount} to the green account from main account."
        bunq_result = await bunq_agent.run(bunq_prompt, deps=deps)
        print(bunq_result.output)

        motivational_prompt = (
            f"I just transferred {offset_amount:.2f} Euros to offest my CO2 emission. "
            "What’s something inspiring I can compare it to?"
        )
        motivation_result = await motivation_agent.run(motivational_prompt, deps=deps)
        print("\n🌟 Motivation Insight:\n", motivation_result.output)
        motivation_qote = motivation_result.output
        return {
            "habits_output": response.output,
            "user_spending": user_spending,
            "co2_output": footprint_result.output,
            "offset_amount": offset_amount,
            "green_balance": bunq_result.output.green_account_balance,
            "motivation": motivation_qote
        }


if __name__ == '__main__':
    asyncio.run(main())
