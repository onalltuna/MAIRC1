#from dialog.dialog_manager import xxx



responses = {

# {givenfoodtype}
# {correctedfoodtype}
# {givenrestaurant}

# {last_response}

#ask more info
    "askpricerange": "Which price range do you prefer?",
    "reqalts_re": "rhfg",
    "reqmore_re": "rhfg",
    "request_re": "rhfg",

#confirm info
    "confirmfoodtype": "Sorry, I do not recognize {givenfoodtype}. Did you mean {correctedfoodtype}?",

#ack preferences
    "ack_re": "rgd",
    "affirm_re": "rhfg",
    "confirm_re": "rhfg",

#repeat previous answer
#last response stored in dialog_manager
#    "repeat_re": "Yes, of course. {last_response}", 

#inform is handeled in the other folder? right? 
#"inform_re": "xxx",

#deny/no
    "deny_re_food": "I understand, you do not want {givenfoodtype}. What would you like to eat instead?",
    "deny_re_price": "I understand, you do not want {givenprice}. What price are you looking for instead?", 
    "deny_re_area": "I understand, you do not want {givenarea}. What are you looking for instead?",    

    "negate_re_food": "Sorry, I understand you want {givenfoodtype} instead. I will look for that instead",
    "negate_re_food": "rhfg",

#input unclear/null
    "null_re": "Sorry, I did not understand. Could you repeat yourself?",



}