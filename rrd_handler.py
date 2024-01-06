""" Kinetic - Handler for creating/updating RRD files. """

from hashlib import md5
from pathlib import Path
from typing import Union
from pydantic import BaseModel, field_validator, Field
from rrdtool import update, create

class RRDHandler(BaseModel):
    """
    Model for creating/updating RRD files.

    Attributes:
        agent_id (int): ID of the agent
        monitor_id (int): ID of the monitor
        step (int): RRD step in seconds
        results (list[int]): List of latency results
    """

    agent_id: int = Field(..., gt=0)
    monitor_id: int = Field(..., gt=0)
    step: int = Field(..., gt=0, le=3600, description="RRD step in seconds")
    results: list[Union[float, str]] = Field(..., description="List of latency results")

    @field_validator("results")
    def check_results(cls, v):
        """ Check if results is a float, int or 'U' """
        for i in v:
            if i != "U":
                try:
                    float(i)
                except ValueError as exc:
                    raise ValueError("Results must be a float, int or 'U'") from exc
        return v

    def __init__(self, **data):
        """ Create/update RRD file """
        super().__init__(**data)
        agent_id = self.agent_id
        monitor_id = self.monitor_id
        step = self.step
        results = self.results
        rrd_file = "rra_data/" + md5((str(agent_id) + "-" + str(monitor_id)).encode()).hexdigest() + ".rrd"

        #print(f"agent_id: {agent_id}\nmonitor_id: {monitor_id}\nstep: {step}\nresults: {results}\nrrd_file: {rrd_file}")

        # use pathlib to check if file exists
        if Path(rrd_file).is_file():
            RRDHandler.rrd_update(agent_id=agent_id, results=results, rrd_file=rrd_file)
        else:
            Path("rra_data").mkdir(parents=True, exist_ok=True)
            RRDHandler.rrd_create(agent_id=agent_id, step=step, results=results, rrd_file=rrd_file)

    def rrd_create(agent_id: int, step: int, results: list[Union[float, str]], rrd_file: str):
        """
        Kinetic - Create RRD file with Kinetic results.

        Args:
            agent_id (int): ID of the agent
            results (list[int]): List of latency results
            rrd_file (str): Path to RRD file
            step (int): RRD step in seconds
        """

        rrd = []
        rrd.append(rrd_file)
        rrd.append("--start")
        rrd.append("now-2h")
        rrd.append("--step")
        rrd.append(f"{step}")
        rrd.append(f"DS:loss:GAUGE:{step*2}:0:{len(results)}")
        rrd.append(f"DS:median:GAUGE:{step*2}:0:180")
        for i in range(1, len(results)+1):
            rrd.append(f"DS:result{i}:GAUGE:{step*2}:0:180")
        rrd.append("RRA:AVERAGE:0.5:1:1008")
        rrd.append("RRA:AVERAGE:0.5:12:4320")
        rrd.append("RRA:MIN:0.5:12:4320")
        rrd.append("RRA:MAX:0.5:12:4320")
        rrd.append("RRA:AVERAGE:0.5:144:720")
        rrd.append("RRA:MAX:0.5:144:720")
        rrd.append("RRA:MIN:0.5:144:720")

        # create RRD file
        create(rrd)

    def rrd_update(agent_id: int, results: list[Union[float, str]], rrd_file: str):
        """
        Kinetic - Update RRD file with Kinetic results.
        
        Args:
            agent_id (int): ID of the agent
            results (list[int]): List of latency results
            rrd_file (str): Path to RRD file
        """
        rrd = []
        rrd.append(rrd_file)
        rrd.append("--template")

        rrd_names = "loss:median"

        # calculate loss and median
        rrd_loss = 0
        rrd_median = 0
        for i in results:
            if i == "U":
                rrd_loss += 1
            else:
                rrd_median += i
        rrd_median = round(rrd_median / len(results), 3)

        rrd_vals = f"N:{rrd_loss}:{rrd_median}"

        # individual results
        for i in range(1, len(results)+1):
            rrd_names += f":result{i}"
            if results[i-1] is None:
                rrd_vals += ":NaN"
            else:
                rrd_vals += f":{results[i-1]}"

        rrd.append(rrd_names)
        rrd.append(rrd_vals)

        # update RRD file
        update(rrd)
