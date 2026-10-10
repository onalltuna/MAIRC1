RESPONSES = {

    "welcome":
        "Hello, welcome to the Cambridge restaurant recommendation system. How may I help you?",

    "askfood":
        "What type of food would you like?",

    "askpricerange":
        "Which price range do you prefer?",

    "askarea":
        "What part of town would you prefer?",
    "ask_additional":
        "I found some restaurants matching your preferences. Do you have any additional requirements?",

    "unrecognized_preference": "Sorry, I am not familiar with this preference. Would you like something else?",

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

    "confirm_yes":
        "Yes, that's correct.",

    "confirm_no":
        "No, the {field} is actually {actual_value}.",

    "nomatch":
        "Sorry, I couldn't find a restaurant matching your preferences: food={food}, area={area}, pricerange={pricerange}",
    "nomatch_requirement":
        "Sorry, none of the restaurants matching your preferences {requirement}.",
    "nomatchfound":"Sorry, I couldn't find a restaurant matching your preferences.",
    "recommend":
        "I recommend {restaurantname}. "
        "It serves {food} food, is in the {area} area, "
        "and is in the {pricerange} price range.",

    "alternative":
        "How about {restaurantname}? It serves {food} food, is in the {area} area, and is in the {pricerange} price range.",

    "noalternative":
        "Sorry, there are no more restaurants matching your preferences.",

    "restart":
        "Let's start over.",
    "postcode": "Postcode of {restaurantname} is {postcode}.",
    "address": "The address of {restaurantname} is: {address}.",
    "phone": "Phone number of {restaurantname} is {phone}.",
    "restaurant_info": "Restaurant {restaurantname} is available. Would you like the address, phone number, or postcode?",
    "restaurant_info_unknown": "The {info} of {restaurantname} is unknown.",
    "acknowledge": "Okay",
    "offer_preference_change":"I'm afraid that's all the options I have. Would you like to change a preference?",
    "ask_preference_change": "What preference would you like to change?",
    "goodbye":
        "Goodbye!",
    "ended":
        "The conversation has ended.",
    "repeat": "Could please be more elaborate on that.",





    "nothing_to_change": "Okay, I'll keep your preferences. Would you like the address, phone number, or postcode of {restaurantname}?",
    "anything_else": "Okay. Is there anything else I can help you with?",
    "rejected_ack": "Okay, I won't suggest {restaurantname} again.",
    "confirm_unclear": "Sorry, I didn't understand. Could you rephrase?",
    "fallback": "Sorry, I didn't catch that. Could you rephrase?"

}

def response(key, **kwargs):
    if "restaurantname" in kwargs and kwargs["restaurantname"]:
        kwargs["restaurantname"] = kwargs["restaurantname"].capitalize()

    template = RESPONSES[key]
    return template.format(**kwargs)