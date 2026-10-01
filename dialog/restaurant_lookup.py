# dialog/restaurant_lookup.py

import csv


def find_restaurants(
    food=None,
    price=None,
    area=None,
    csv_path="dialog/restaurant_info.csv",
):
    """
    Find restaurants matching the user's confirmed preferences.

    Returns a list of matching restaurants.
    """

    matches = []

    with open(csv_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for restaurant in reader:

            if food is not None:
                if restaurant["food"].strip().lower() != food.strip().lower():
                    continue

            if price is not None:
                if restaurant["pricerange"].strip().lower() != price.strip().lower():
                    continue

            if area is not None:
                if restaurant["area"].strip().lower() != area.strip().lower():
                    continue

            matches.append(restaurant)

    return matches