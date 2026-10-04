# dialog/restaurant_lookup.py

import csv


PRICE_KEYWORDS = {
    "cheap": {"cheap", "inexpensive", "budget", "affordable"},
    "moderate": {"moderate", "moderately", "mid-range", "average", "reasonably priced"},
    "expensive": {"expensive", "pricey", "high-end", "expensively"},
}

def find_restaurants(
    food=None,
    price=None,
    area=None,
    csv_path="dialog/restaurant_info_extended.csv",
):
    """
    Find restaurants matching the user's confirmed preferences.

    Returns a list of matching restaurants.
    """

    matches = []

    with open(csv_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for restaurant in reader:

            if food is not None and food.lower() != "any":
                restaurant_food = (restaurant.get("food") or "").strip().lower()

                if restaurant_food != food.strip().lower():
                    continue

            if price is not None and price.lower() != "any":
                for keyword in PRICE_KEYWORDS:
                    if price in PRICE_KEYWORDS[keyword]:
                        price = keyword
                restaurant_price = (restaurant.get("pricerange") or "").strip().lower()

                if restaurant_price != price.strip().lower():
                    continue

            if area is not None and area.lower() != "any":
                if area == "center":
                    area = "centre"
                restaurant_area = (restaurant.get("area") or "").strip().lower()

                if restaurant_area != area.strip().lower():
                    continue

            matches.append(restaurant)

    return matches