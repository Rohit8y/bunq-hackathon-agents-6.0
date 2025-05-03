import os
import asyncio
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic import BaseModel
from dataclasses import dataclass
from dotenv import dotenv_values
from dotenv import load_dotenv
import datetime
import random
from httpx import AsyncClient
from pydantic import BaseModel, Field
from typing import Dict, List

load_dotenv()
config = dotenv_values(".env")

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

get_user_habits_agent = Agent(
    model,
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
        response = await get_user_habits_agent.run(
            "Can you analyze my recent spending patterns and tell me where my money is going?",
            deps=deps
        )
        print("\n--- User Habits Agent Analysis Result ---")
        print("\nSpending Summary Text:")
        print(response.output.spending_summary_text)
        print("\nCategory Percentage Distribution:")
        print(response.output.category_percentage_distribution)

if __name__ == '__main__':
    asyncio.run(main())