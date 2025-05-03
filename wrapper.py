from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType
import os
from dotenv import load_dotenv
from bunq.sdk.model.generated.endpoint import PaymentApiObject
from bunq.sdk.model.generated.object_ import AmountObject, PointerObject
from bunq.sdk.model.generated.endpoint import RequestInquiryApiObject
from bunq import Pagination
from bunq.sdk.model.generated.endpoint import MonetaryAccountBankApiObject

load_dotenv()

sandbox_key = os.getenv("BUNQ_SANDBOX_API_KEY")


def request_money_from_sugar_daddy(amount: float, currency: str = "EUR", description: str = "You're the best!") -> int:
    # Validate amount
    if amount <= 0 or amount > 500:
        raise ValueError("Amount must be between 0 and 500")

    amount_str = f"{amount:.2f}"

    request_id = RequestInquiryApiObject.create(
        amount_inquired=AmountObject(amount_str, currency),
        counterparty_alias=PointerObject(
            type_="EMAIL",
            value="sugardaddy@bunq.com",
            name="Sugar Daddy"
        ),
        description=description,
        allow_bunqme=False
    ).value

    return request_id


def list_transactions(monetary_account_id=None, page_size=25):
    pagination = Pagination()
    pagination.count = page_size

    params = {"params": pagination.url_params_count_only}
    if monetary_account_id is not None:
        params["monetary_account_id"] = monetary_account_id

    all_payments = []
    response = PaymentApiObject.list(**params)
    payments = response.value
    all_payments.extend(payments)

    pagination_info = response.pagination
    while pagination_info.has_next_page_assured():

        next_page_params = {"params": pagination_info.url_params_next_page}
        if monetary_account_id is not None:
            next_page_params["monetary_account_id"] = monetary_account_id

        response = PaymentApiObject.list(**next_page_params)
        next_page_payments = response.value
        all_payments.extend(next_page_payments)

        pagination_info = response.pagination

    formatted_transactions = []
    for payment in all_payments:
        transaction = {
            "id": payment.id_,
            "amount": payment.amount.value,
            "currency": payment.amount.currency,
            "description": payment.description,
            "date": payment.created,
        }
        formatted_transactions.append(transaction)

    return formatted_transactions


def print_transactions(transactions) -> None:
    if not transactions:
        print("No transactions found.")
        return

    print(f"Found {len(transactions)} transactions:")
    print("-" * 80)
    for tx in transactions:
        print(f"ID: {tx['id']}")
        print(f"Date: {tx['date']}")
        print(f"Amount: {tx['amount']} {tx['currency']}")
        print(f"Description: {tx['description']}")
        print("-" * 80)


def create_monetary_account(description: str, currency: str = "EUR") -> int:
    from bunq.sdk.model.generated.endpoint import MonetaryAccountBankApiObject

    # Create a new monetary account
    account_id = MonetaryAccountBankApiObject.create(
        currency=currency,
        description=description
    ).value

    return account_id


def get_all_monetary_accounts():
    # Get all monetary accounts
    accounts = MonetaryAccountBankApiObject.list().value

    # Format account information
    formatted_accounts = []
    for account in accounts:
        formatted_account = {
            "id": account.id_,
            "description": account.description,
            "balance": account.balance.value,
            "currency": account.balance.currency,
            "status": account.status,
            "is_primary": hasattr(account, "is_primary") and account.is_primary
        }
        formatted_accounts.append(formatted_account)

    return formatted_accounts


def print_accounts(accounts) -> None:
    if not accounts:
        print("No accounts found.")
        return

    print(f"Found {len(accounts)} accounts:")
    print("-" * 80)
    for acc in accounts:
        primary_marker = " (PRIMARY)" if acc.get("is_primary", False) else ""
        print(f"ID: {acc['id']}{primary_marker}")
        print(f"Description: {acc['description']}")
        print(f"Balance: {acc['balance']} {acc['currency']}")
        print(f"Status: {acc['status']}")
        print("-" * 80)


def get_account_iban(monetary_account_id: int) -> str:
    account = MonetaryAccountBankApiObject.get(monetary_account_id).value

    for alias in account.alias:
        if alias.type_ == "IBAN":
            return alias.value

    raise ValueError(f"No IBAN found for monetary account ID: {monetary_account_id}")


def transfer_between_accounts(
        from_account_id: int,
        to_account_id: int,
        amount: float,
        currency: str = "EUR",
        description: str = "Transfer between accounts"):
    amount_str = f"{amount:.2f}"

    to_account_iban = get_account_iban(to_account_id)
    to_account = MonetaryAccountBankApiObject.get(to_account_id).value
    to_account_name = to_account.description

    payment_id = PaymentApiObject.create(
        amount=AmountObject(amount_str, currency),
        counterparty_alias=PointerObject(
            type_="IBAN",
            value=to_account_iban,
            name=to_account_name
        ),
        description=description,
        monetary_account_id=from_account_id
    ).value

    return payment_id


if __name__ == "__main__":
    api_context = ApiContext.create(
        ApiEnvironmentType.SANDBOX,
        sandbox_key,
        "My Test Device"
    )

    api_context.save("bunq_sandbox_context.conf")

    BunqContext.load_api_context(api_context)

    print("API context created and saved successfully!")
    print(f"User ID: {BunqContext.user_context().user_id}")

    # request_id = request_money_from_sugar_daddy(100)
    # print(f"Created request with ID: {request_id}")

    # account_id = create_monetary_account("Vacation Savings")
    # print(f"Created new account with ID: {account_id}")

    accounts = get_all_monetary_accounts()

    # transactions = list_transactions("2108117")

    # print_transactions(transactions)

    # iban = get_account_iban("2112229")

    # transfer_between_accounts("2108116","2112229",200.0,)













