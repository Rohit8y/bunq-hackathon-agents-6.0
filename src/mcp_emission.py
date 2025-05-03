from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import requests
from pydantic import BaseModel, Field,field_validator
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
import json
load_dotenv()

sandbox_key = os.getenv("BUNQ_API_KEY")

mcp = FastMCP("Green MCP Server",host="0.0.0.0", port=8009)


from dataclasses import dataclass

@dataclass
class Transaction:
    description: str
    amount: float
    currency: str

@dataclass
class EcoResult:
    total_co2: float
    co2_per_euro: float
    zone: str

class OffsetRecommendation(BaseModel):
    recommended_donation_eur: float
    message: str


@mcp.tool()
def improve_carbon_footprint(eco_res: EcoResult) -> OffsetRecommendation:
    '''
    eco_res is a dataclass objects of EcoResult
    Generates what the user could do to improve his carbon footprint by personalized donation recommendations and carbon offset impact information
    based on the user's spending patterns and carbon footprint analysis.
    
    Parameters:
    -----------
    eco_res : EcoResult
        The carbon footprint analysis results containing:
        - total_co2 (float): Total carbon emissions in kg CO₂
        - co2_per_euro (float): Average carbon intensity per euro spent
        - zone (str): Sustainability classification ('Green', 'Yellow', or 'Red')
    
    Returns:
    --------
    float: Recommended donation amount in euros to offset the carbon footprint
    '''
    if eco_res.zone == "Red":
        donation = 80
        msg = "Your carbon footprint is high. Consider donating €80 to offset it."
    elif eco_res.zone == "Yellow":
        donation = 60
        msg = "Your carbon footprint is moderate. A €60 donation is suggested to improve sustainability."
    else:
        donation = 20
        msg = "Great job! You're in the green zone. A small €20 donation can fully offset your footprint."
    
    return OffsetRecommendation(recommended_donation_eur=donation, message=msg)
    

@mcp.prompt()
def analyse_spending_patterns(transactions):
    """
    This function prepares instructions for a financial assistant to examine spending behavior
    based on categorized transaction data from the past 20 days. The analysis focuses on identifying
    major expense areas, detecting spending patterns, and recommending actionable savings strategies.
    """

    prompt_instructions = (
        f"You are a financial coach analyzing recent transactions from a user's account.\n"
        f"The transactions are as follows: {transactions} Using the past 20 days of transaction data (with categories like food_dining, groceries, entertainment, etc.), analyze their spending patterns and provide personalized savings advice.\n"
        f"Your Task:"
        f"1. Analyze spending by category and identify biggest expense areas"
        f"2. Find patterns in timing, frequency, and size of transactions."
        f"3.Recommend 2-3 specific, actionable ways to save money based on actual spending behavior."
        f"4. Quantify potential savings (e.g., 'Cutting entertainment costs by 20% saves $X monthly')"
        )
    return prompt_instructions


@mcp.tool()
def estimate_carbon_footprint(transaction_list : List[Transaction]):
    """
    transaction_list is a list of dataclass objects of Transaction.
    Calculates carbon footprint metrics from transaction data and determines sustainability zone.
    
    This function analyzes financial records to estimate their environmental impact by:
    1. Categorizing spending into predefined CO₂ categories
    2. Applying carbon intensity factors to each category (kg CO₂ per €)
    3. Computing total carbon emissions and carbon efficiency metrics
    4. Determining a sustainability zone (Green, Yellow, or Red)
    
    """


    carbon_factors = {
        'travel_transport': 0.8,
        'food_dining': 0.6,
        'groceries_household': 0.5,
        'shopping_fashion': 0.5,
        'housing_utilities': 0.3,
        'entertainment_subscriptions': 0.3,
        'health_wellness': 0.2,
        'education_books': 0.2,
        'financial_services': 0.1,
        'charity_gifts': 0.05,
        'gifts': 0.05,
        'salary': 0.05  
    }
    

    total_co2 = 0
    total_spent_eur = 0

    for transaction in transaction_list:
        
       
        if transaction.amount >= 0:
            continue
        

        category = transaction.description
        amount = abs(transaction.amount)

        if transaction.currency == "USD":
            amount_eur = amount * 0.85  
        elif transaction.currency == "GBP":
            amount_eur = amount * 1.15  
        else:  
            amount_eur = amount
        

        if category in carbon_factors:
            co2 = amount_eur * carbon_factors[category]
            total_co2 += co2
            total_spent_eur += amount_eur
    

    co2_per_euro = total_co2 / total_spent_eur if total_spent_eur > 0 else 0
    
    if co2_per_euro < 0.4:
        zone = "Green"
    elif 0.4 <= co2_per_euro <= 0.6:
        zone = "Yellow"
    else:
        zone = "Red"

    
    eco_result = EcoResult(
        total_co2=round(total_co2, 2),
        co2_per_euro=round(co2_per_euro, 2),
        zone=zone
    )


    return eco_result
    

if __name__ == "__main__":
    mcp.run(transport="sse")