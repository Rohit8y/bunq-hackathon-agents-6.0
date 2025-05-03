EMISSION_FACTORS_10 = {
    'travel_transport': 0.8,
    'food_dining': 0.6,
    'groceries_household': 0.5,
    'shopping_fashion': 0.5,
    'housing_utilities': 0.3,
    'entertainment_subscriptions': 0.3,
    'health_wellness': 0.2,
    'education_books': 0.2,
    'financial_services': 0.1,
    'charity_gifts': 0.05
}

# Mapping of raw categories to the 10 broad categories
CATEGORY_MAPPING = {
    # travel & transport
    'TRAVEL': 'travel_transport', 'TRANSPORT': 'travel_transport', 'CAR_EXPENSES': 'travel_transport',
    'FUEL': 'travel_transport', 'HOTEL_STAY': 'travel_transport', 'HOTELS': 'travel_transport',
    'ACCOMMODATION': 'travel_transport', 'ACCOMODATION': 'travel_transport', 'BOOKING': 'travel_transport',
    'RENT_AND_UTILITIES': 'housing_utilities', 'RENDS_AND_UTILITIES': 'housing_utilities',

    # food & dining
    'FOOD_AND_DRINK': 'food_dining', 'FOOD_ANDROID_DRINK': 'food_dining', 'DINING': 'food_dining',
    'DINING_OUT': 'food_dining', 'RESTAURANT': 'food_dining', 'RESTAURANTS': 'food_dining',
    'RESTAURANTS_AND_BARS': 'food_dining', 'COFFEE_SHOPS': 'food_dining', 'COFFEE_SHOP': 'food_dining',
    'COFFEE_AND_TEA': 'food_dining', 'COFFEE_AND_SNACKS': 'food_dining', 'CAFE': 'food_dining',
    'CAFES': 'food_dining', 'FAST_FOOD': 'food_dining', 'FAST_FOODS': 'food_dining',
    'VEGETARIAN_RESTAURANT': 'food_dining', 'BAKERY': 'food_dining',

    # groceries & household
    'GROCERIES': 'groceries_household', '             GROCERIES': 'groceries_household',
    'HOUSEHOLD_EXPENSES': 'groceries_household', 'HOME_EXPENSES': 'groceries_household',
    'FURNITURE': 'groceries_household', 'FURNITURE_SHOPPING': 'groceries_household',
    'FURNISHING': 'groceries_household', 'HOME_IMPROVEMENT': 'groceries_household',
    'UTILITIES': 'housing_utilities', 'UTILITY': 'housing_utilities', 'UTILITY_BILLS': 'housing_utilities',
    'BILLS': 'housing_utilities', 'BILLS_AND_UTILITIES': 'housing_utilities', 'MONTHLY_BILLS': 'housing_utilities',

    # shopping & fashion
    'SHOPPING': 'shopping_fashion', 'SHOOPING': 'shopping_fashion', 'ONLINE SHOPPING': 'shopping_fashion',
    'ONLINE_SHOPPING': 'shopping_fashion', 'ONLINE_PURCHASES': 'shopping_fashion', 'ONLINE': 'shopping_fashion',
    'FASHION & CLOTHING': 'shopping_fashion', 'CLOTHING': 'shopping_fashion', 'SHOPS': 'shopping_fashion',
    'TOYS': 'shopping_fashion', 'COSMETICS': 'shopping_fashion', 'PERSONAL_CARE': 'shopping_fashion',
    'PRSONAL_CARE': 'shopping_fashion', 'LIFESTYLE': 'shopping_fashion', 'TECHNOLOGY': 'shopping_fashion',

    # housing & utilities
    'HOUSING': 'housing_utilities', 'HOUSING_EXPENSES': 'housing_utilities', 'INTERNET_EXPENSES': 'housing_utilities',
    'PHONE_ONLINE': 'housing_utilities', 'GARDENING': 'housing_utilities',

    # entertainment & subscriptions
    'ENTERTAINMENT': 'entertainment_subscriptions', 'ENETRTAINMENT': 'entertainment_subscriptions',
    'GAMES': 'entertainment_subscriptions', 'GAMING': 'entertainment_subscriptions',
    'STREAMING_SERVICES': 'entertainment_subscriptions', 'SUBSCRIPTION': 'entertainment_subscriptions',
    'SUBSCRIPTIONS': 'entertainment_subscriptions', 'MUSIC': 'entertainment_subscriptions',
    'CULTURE': 'entertainment_subscriptions', 'ART': 'entertainment_subscriptions',
    'ARTS_AND_CRAFTS': 'entertainment_subscriptions', 'EDITORIAL': 'entertainment_subscriptions',

    # health & wellness
    'HEALTHCARE': 'health_wellness', 'SPORTS': 'health_wellness', 'INSURANCE': 'health_wellness',

    # education & books
    'BOOKS': 'education_books', 'BOOK': 'education_books', 'BOOK_STORE': 'education_books',
    'BOOKSTORE': 'education_books', 'BOOKS_AND_EDUCATION': 'education_books',
    'BOOKS_AND_LITERATURE': 'education_books', 'BOOKS_AND_MEDIA': 'education_books',
    'BOOKS_AND_MAGAZINES': 'education_books', 'BOOKS_AND_ZINE': 'education_books', 'EDUCATION': 'education_books',

    # financial & professional services
    'FINANCE': 'financial_services', 'FAINANCE': 'financial_services', 'EXPENSES': 'financial_services',
    'EXPENSE': 'financial_services', 'BUSINESS_EXPENSES': 'financial_services',
    'PROFESSIONAL_SERVICES': 'financial_services', 'LEGAL': 'financial_services', 'LEGAL_FEES': 'financial_services',
    'TAX': 'financial_services', 'TAXES': 'financial_services', 'TAX_PAYMENTS': 'financial_services',
    'SALARY': 'financial_services', 'PAYROLL': 'financial_services', 'SOFTWARE': 'financial_services',
    'INVESTMENTS': 'financial_services', 'ASSETS': 'financial_services', 'INCOME': 'financial_services',
    'EXTRA_INCOME': 'financial_services', 'REVENUE': 'financial_services', 'PAYMENT': 'financial_services',
    'TRANSFER': 'financial_services', 'TRANSFERS': 'financial_services', 'EXCHANGE': 'financial_services',
    'CASH': 'financial_services', 'GENERAL': 'financial_services', 'GENARAL': 'financial_services',
    'UNCATEGORIZED': 'financial_services',

    # charity & donations
    'DONATIONS': 'charity_gifts', 'DONATION': 'charity_gifts', 'CHARITY': 'charity_gifts',
    'GIFTS': 'charity_gifts', 'FAMILY': 'charity_gifts', 'BONUS': 'charity_gifts',
    'GROUP_EXPENSE': 'charity_gifts', 'HR': 'charity_gifts', 'EMPLOYEE_BENEFITS': 'charity_gifts',
    'GOVERNMENT': 'charity_gifts', 'LOCAL_GOVERNMENT': 'charity_gifts', 'GOVERNMENT_PAYMENT': 'charity_gifts'
}