import logging

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

sandbox_key = os.getenv("BUNQ_API_KEY")


class Bunq_SDK_Wrapper():
    def __init__(self, context_file="bunq_sandbox_context.conf"):

        self.api_context = None
        if not os.path.exists(context_file):
            logger.info("Creating new API context, could not find old file")
            self.api_context = ApiContext.create(
                ApiEnvironmentType.SANDBOX,
                sandbox_key,
                "My Test Device"
            )

            self.api_context.save(context_file)
        else:
            logger.info("Existing API context found, restoring...")
            self.api_context = ApiContext.restore(context_file)

        BunqContext.load_api_context(self.api_context)
        self.user_context = BunqContext.user_context()
        self.user_id = BunqContext.user_context().user_id

        logger.info(f"User ID: {BunqContext.user_context().user_id}")

    @staticmethod
    def get_all_accounts():
        # Get all monetary accounts
        accounts = MonetaryAccountBankApiObject.list().value
        return accounts

    def get_main_account_balance(self):
        balance = self.user_context.primary_monetary_account.balance.value
        return balance

    def get_main_account(self):
        return self.user_context.primary_monetary_account

    @staticmethod
    def get_account_balance(account_id: int):
        account_info = MonetaryAccountBankApiObject.get(account_id).value
        return account_info.balance.value

    @staticmethod
    def get_account_details(account_id: int):
        account_info = MonetaryAccountBankApiObject.get(account_id).value
        return account_info

    def get_green_account(self):
        all_accounts = self.get_all_accounts()
        for account in all_accounts:
            if account.description == "Green":
                return account
        return None

    @staticmethod
    def get_account_iban(monetary_account_id: int) -> str:
        account = MonetaryAccountBankApiObject.get(monetary_account_id).value

        for alias in account.alias:
            if alias.type_ == "IBAN":
                return alias.value

        raise ValueError(f"No IBAN found for monetary account ID: {monetary_account_id}")

    @staticmethod
    def create_monetary_account(description: str, currency: str = "EUR") -> int:

        # Create a new monetary account
        account_id = MonetaryAccountBankApiObject.create(
            currency=currency,
            description=description
        ).value

        return account_id

    @staticmethod
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

    def transfer_between_accounts(self,
                                  from_account_id: int,
                                  to_account_id: int,
                                  amount: float,
                                  currency: str = "EUR",
                                  description: str = "Transfer between accounts"):
        amount_str = f"{amount:.2f}"

        to_account_iban = self.get_account_iban(to_account_id)
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

    @staticmethod
    def list_transactions(monetary_account_id=None, page_size=10):
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


if __name__ == "__main__":
    obj = Bunq_SDK_Wrapper()
    # obj.request_money_from_sugar_daddy(amount=400)
    accounts = obj.get_all_accounts()
    green_account = obj.get_green_account()
    account = obj.get_account_details("2113198")

    # logger.info(obj.get_account_balance("2112229"))
