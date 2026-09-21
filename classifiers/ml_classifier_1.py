#TODO in this file first ML classifier should be defined, its train function should reach the train data in data folder and train the model
#when the model is trained, it should be saved under classifiers folder. When the test funcion is called it should load the respective model from 
# classifiers folder and reach the test data from data folder and apply the testing logic

def train(isGrouped):
    print("you are running the train proccess for ML1")
    print(f"isGrouped: {isGrouped}")


def test(isHeldOut, isGrouped):
    print("you are testing ML1")
    print(f"isHeldOut: {isHeldOut}, isGrouped: {isGrouped}")