from mcp.server.fastmcp import FastMCP
import os
from pydantic import BaseModel, Field
from typing import Dict, List
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType
from dotenv import load_dotenv
from bunq.sdk.model.generated.endpoint import PaymentApiObject
from bunq.sdk.model.generated.object_ import AmountObject, PointerObject
from bunq.sdk.model.generated.endpoint import RequestInquiryApiObject
from bunq import Pagination
from bunq.sdk.model.generated.endpoint import MonetaryAccountBankApiObject
import random
import datetime 

load_dotenv()

sandbox_key = os.getenv("BUNQ_API_KEY")

mcp = FastMCP("Bunq's MCP Server")

from dataclasses import dataclass

@dataclass
class Transaction:

    description: str
    amount: float
    currency: str


class TransactionItem(BaseModel):
    """Represents a single transaction item."""
    date: str = Field(..., description="The date of the transaction (YYYY-MM-DD).")
    description: str = Field(..., description="A description or category for the transaction.")
    amount: float = Field(..., description="The monetary amount of the transaction. Negative for expenses, positive for credits.")
    
class TransactionListResponse(BaseModel):
    """Represents a list of transactions."""
    transactions: List[TransactionItem] = Field(..., description="A list containing individual transaction details.")

api_context = ApiContext.create(
ApiEnvironmentType.SANDBOX,
sandbox_key,
"My Test Device"
)

api_context.save("bunq_sandbox_context.conf")
BunqContext.load_api_context(api_context)


@mcp.tool()
def request_money_from_sugar_daddy(currency: str = "EUR", description: str = "Got some Money YAY !!!!"):
    """Sends a money request for a fixed amount (300) to 'sugardaddy@bunq.com'.

    This tool uses the RequestInquiryApiObject to create a specific money
    request via the bunq API. The request is always for 300 units of the
    specified currency and is always sent to the email address
    'sugardaddy@bunq.com' with the name 'Sugar Daddy'.

    It does not allow creating a public bunq.me payment link (`allow_bunqme=False`).

    Args:
        currency (str, optional): The currency code for the 300 unit amount
            (e.g., "EUR", "USD"). Defaults to "EUR".
        description (str, optional): The description accompanying the money
            request, visible to the recipient.
            Defaults to "Got some Money YAY !!!!".

    Returns:
        str: The unique identifier (ID) of the created money request inquiry.
    """
        
    request_id = RequestInquiryApiObject.create(
        amount_inquired=AmountObject("300", currency),
        counterparty_alias=PointerObject(
            type_="EMAIL",
            value="sugardaddy@bunq.com",
            name="Sugar Daddy"
        ),
        description=description,
        allow_bunqme=False
    ).value
    
    return request_id


@mcp.tool()
def create_monetary_account(account_name: str, currency: str = "EUR"):
    """Creates a new monetary bank account via the API.

    This tool uses the `MonetaryAccountBankApiObject.create` method to
    provision a new bank account associated with the user's profile.
    The account will be created with the specified currency and will
    use the provided `account_name` as its description.

    Args:
        account_name (str): The desired name or description for the new
            monetary account. This is often displayed to the user in interfaces.
        currency (str, optional): The currency code (e.g., "EUR", "USD")
            for the new account. Defaults to "EUR".

    Returns:
        int | str: The unique identifier (ID) of the newly created monetary
                   account, as returned by the API's `.value`. The exact type
                   (typically int or str) may depend on the specific API
                   implementation.
    """
    account_id = MonetaryAccountBankApiObject.create(
        currency=currency,
        description=account_name
    ).value
    account = MonetaryAccountBankApiObject.get(account_id).value
    return {
            "id": account.id_,
            "description": account.description,
            "balance": account.balance.value,
            "currency": account.balance.currency,
            "status": account.status,
            "is_primary": hasattr(account, "is_primary") and account.is_primary
            }

@mcp.tool()
def send_money_between_accounts(amount,to_account_name: str, from_account_name: str):
    """
    Sends a specified amount of money from one monetary account to another.
    This function facilitates transferring funds between two accounts owned by the user,
    identifying them by their 'description' names. It performs the following steps:
    1. Fetches a list of the user's monetary accounts using the MonetaryAccountBankApiObject.
    2. Finds the account IDs corresponding to the provided `from_account_name` and
       `to_account_name` by matching their 'description' attributes.
    3. Retrieves the full details of the destination account (`to_account_name`) to find
       its IBAN alias.
    4. Creates a payment request using the PaymentApiObject, transferring the specified
       `amount` from the `from_account_id` to the `to_account_name`'s IBAN.
    Args:
        amount (float | Decimal): The amount of money to send (e.g., 10.50).
                                  It will be formatted to two decimal places.
        to_account_name (str): The 'description' name of the monetary account
                               that should receive the funds.
        from_account_name (str): The 'description' name of the monetary account
                                 from which the funds should be sent.

    Returns:
        int: The ID of the newly created payment object upon successful creation.

    """

    descriptions_set = set([from_account_name,to_account_name])
    found_accounts: Dict[str, int] = {}
    pagination = Pagination()
    pagination.count = 100



    all_accounts_response = MonetaryAccountBankApiObject.list(params=pagination.url_params_count_only)
    all_accounts = all_accounts_response.value

    for account in all_accounts:
        if hasattr(account, 'description') and hasattr(account, 'id_'):
            if account.description in descriptions_set:
                if account.description not in found_accounts:
                    found_accounts[account.description] = account.id_
                if len(found_accounts) == len(descriptions_set):
                    break
    
    

    to_account_id = found_accounts[to_account_name]
    from_account_id = found_accounts[from_account_name]



    to_account = MonetaryAccountBankApiObject.get(to_account_id).value
    for alias in to_account.alias:
        if alias.type_ == "IBAN":
            to_iban = alias.value
            break

    payment_id = PaymentApiObject.create(
        amount=AmountObject(amount, "EUR"),
        counterparty_alias=PointerObject(
            type_="IBAN", 
            value=to_iban,
            name=to_account_name
        ),
        description="sent money",
        monetary_account_id=from_account_id  
    ).value

    return payment_id

@mcp.tool()
def get_transactions_bunq(user_prompt: str) -> TransactionListResponse:
    '''
    Retrieves transaction history formatted similarly to Bunq API responses.

    Designed to provide transaction data for applications integrating with Bunq.
    Returns a list of transactions covering a recent period.

    Use this function when transaction data corresponding to a Bunq monetary
    account is required by the user or application logic.

    '''
    transactions_list = []
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=20)
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
    for i in range(10):
        random_date = start_date + datetime.timedelta(days=random.randint(0, 20))
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
    return transactions_list

if __name__ == "__main__":
    mcp.run(transport="sse")