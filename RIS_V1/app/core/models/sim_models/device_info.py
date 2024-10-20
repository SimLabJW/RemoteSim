DRONE = {
    "ID" : [1,2,3],
    "Store" : "None",
    "Home" : "None",
    "State" : "None"
}

CAR = {
    "ID" : [1,2,3],
    "Store" : "None",
    "Home" : "None",
    "State" : "None"
}

TRANSITIONS = {
        "STAY": {"STAY": 90, "DELIVERY": 10},
        "DELIVERY": {"DELIVERY": 99.8, "ACCIDENT": 0.1, "CANCEL": 0.1},
        "ACCIDENT": {"ACCIDENT": 100},
        "CANCEL": {"STAY": 100}
}