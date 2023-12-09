""" rrd_handler.py - test script """

from random import  randrange
from json import dumps as json_dumps
from rrd_handler import RRDHandler

if __name__ == "__main__":
    
    # Create a loop that runs twice
    for i in range(2):
        
        data = {
            "agent_id": randrange(1, 10),
            "monitor_id": randrange(1, 100),
            "step": randrange(1, 3600),
            "results": [randrange(1, 100) for _ in range(randrange(1, 35))]
        }

        #rrd_input = RRDHandlerModel(**data)
        #rrd_input = rrd_handler.RRDHandlerModel(**data)
        #print(rrd_input)

    RRDHandler(agent_id=1, monitor_id=1, step=60, results=[20.0, 76.0, 'U', 81.0, 28.0, 26.0, 50.0, 42.0, 96.0, 76.0, 45.0, 22.0, 90.0])
    #, rrd_file="rra_data/a31db89d9c96c85c4940ce27995692aa.rrd")
