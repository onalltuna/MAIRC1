# note: {restaurant_result} needs to come from dialog_manager! or whereever the found restautant is handeled. 

responses = {

# {givenfoodtype}
# {givenprice}
# {givenarea}


# {correctedfoodtype}
# {givenrestaurant}
# {correctedprice}
# {correctedarea}

#{restautant_foodtype}
#{restaurant_price}
#{restaurant_area}

# {last_response}
# {restaurant_result}

#ask more info responses / inform
    "ask_food_type": "Which type of food would you like to eat?",
    "ask_price_range": "Which price range do you prefer?",
    "ask_area": "Which area would you prefer?",

    "reqalts_re_food": "Sure, I can look for {givenfoodtype} food.",
    "reqalts_re_price": "Sure, I can look for something in the {givenprice} price range.",
    "reqalts_re_area": "Sure, I can look for something in the {givenarea} part of town.",

    #more info response 3 way combos
    "reqalts_re_combo_food_area_price": "Sure, I can look for {givenfoodtype} in the {givenarea} with {givenprice}. Is that all? ",


    "reqalts_re_combo_food_area": "Sure, I can look for {givenfoodtype} food in the {givenarea}. What is your preferred price range?",

    "reqalts_re_combo_price_area": "Sure, I can look for {givenprice} price range in the {givenarea}. What is your preferred cuisine?",

    "reqalts_re_combo_food_price": "Sure, I can look for {givenfoodtype} food in the {givenprice} price range. Which area do you prefer?",
    
    
    


    #"reqmore_re": "xxx",
    #"request_re": "xxx",

#confirm info
    "confirm_foodtype": "Sorry, I do not recognize {givenfoodtype}. Did you mean {correctedfoodtype}?",
    "confirm_price": "Sorry, I do not recognize {givenprice}. Did you mean {correctedprice}?",
    "confirm_area": "Sorry, I do not recognize {givenarea}. Did you mean {correctedarea}?",    

#affirm confirm preferences
    "affirm_re": "Nice! Is there anything else you would like to know?",

    "confirm_re_yes": "Yes, {givenrestaurant} is {confirmedvalue}.",
    "confirm_re_no": "No, {givenrestaurant} is {actualvalue}, not {confirmedvalue}.",

#repeat previous answer
#last response stored in dialog_manager
#    "repeat_re": "Yes, of course. {last_response}", 



#deny/no
    "deny_re_food": "I understand, you do not want {givenfoodtype}. What would you like to eat instead?",
    "deny_re_price": "I understand, you do not want {givenprice}. What price are you looking for instead?", 
    "deny_re_area": "I understand, you do not want {givenarea}. What place or area are you looking for instead?",    

    #"negate_re_food": "Sorry, I understand you would like {givenfoodtype} instead. Is that right?", #what else to put?
    #"negate_re_price": "Sorry, I understand you are looking for something in the {givenprice} price range. Is that right?", #what else to put?
    #"negate_re_area": "Sorry, I understand you are looking for something in the {givenarea}. Is that right?", #what else to put?

#input unclear/null
    "null_re": "Sorry, I did not understand. Could you repeat yourself, or could you reword your preference?",


#match and no match
    "match":"I think I found a match! What about {restaurant_result}? It serves {restautant_foodtype} food, is in the {restaurant_price} price range and is in the {restaurant_area}! Does this sound good to you?",

    "no_match":"Unfortunately, I have not found a restaurant match yet. Would you like to search for another food type, area or price range?",

#thanks reply
    "no_problem": "No problem, I'm happy to help!"

}