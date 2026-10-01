RESPONSES = {

    "welcome":
        "Welcome! What kind of restaurant are you looking for?",

    "askfood":
        "What type of food would you like?",

    "askpricerange":
        "Which price range do you prefer?",

    "askarea":
        "Which area do you prefer?",

    "confirmfoodtype":
        "I did not recognize {givenfoodtype}. "
        "Did you mean {correctedfoodtype}?",

    "confirmpricerange":
        "I did not recognize {givenpricerange}. "
        "Did you mean {correctedpricerange}?",

    "confirmarea":
        "I did not recognize {givenarea}. "
        "Did you mean {correctedarea}?",

    "confirmslot":
        "I did not recognize {givenslot}. "
        "Did you mean {correctedslot}?",

    "confirmyesno":
        "Please answer yes or no.",

    "nomatch":
        "Sorry, I couldn't find a restaurant matching your preferences.",

    "recommend":
        "I recommend {restaurantname}. "
        "It serves {food} food, is in the {area} area, "
        "and is in the {pricerange} price range.",

    "alternative":
        "How about {restaurantname}?",

    "noalternative":
        "Sorry, there are no more restaurants matching your preferences.",

    "restart":
        "Let's start over.",
    "postcode": "Postcode is {postcode}",

    "goodbye":
        "Goodbye!",

    "ended":
        "The conversation has ended.",
}


def response(key, **kwargs):
    return RESPONSES[key].format(**kwargs)