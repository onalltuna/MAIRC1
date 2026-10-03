RESPONSES = {

    "welcome":
        "Hello, welcome to the restaurant recommendation system. How may I help you?",

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
    "postcode": "Postcode of {restaurantname} restaurant is {postcode}",
    "address": "The address of {restaurantname} restaurant is {address}",
    "phone": "Phone number of {restaurantname} restaurant is {phone}",
    "restaurant_info": "Restaurant {restaurantname} is available. Would you like the address, phone number, or postcode?",
    "restaurant_info_unknow": "The {info} of {restaurantname} restaurant is unknown.",
    "acknowledge": "Okay",
    "offer_preference_change":"I'm afraid that's all the options I have. Would you like to change a preference?",
    "ask_preference_change": "What preference would you like to change?",
    "goodbye":
        "Good bye!",
    "ended":
        "The conversation has ended.",
}


def response(key, **kwargs):
    return RESPONSES[key].format(**kwargs)