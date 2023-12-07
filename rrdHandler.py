""" Kinetic - Handler for creating/updating RRD files. """

from pathlib import Path
from typing import Any
from pydantic import BaseModel, field_validator, Field
from rrdtool import update, create
import hashlib

class rrdHandler(BaseModel):
    """
    Handler for creating/updating RRD files.
    path: rra_data/<MD5:'agent_id'-'monitor_id>'.rrd
    """

    agent_id: int = Field(..., gt=0)
    monitor_id: int = Field(..., gt=0)
    step: int = Field(..., gt=0, le=3600, description="RRD step in seconds")
    results: list[float] = Field(..., min_items=1, max_items=35, description="List of latency results")

    @field_validator("results")
    def validate_results(cls, v):
        """ Validate results list """
        # length must be between 1 and 35 items
        if len(v) < 1 or len(v) > 35:
            raise ValueError("results must be between 1 and 35 items")
        # each item must be an int or "U"
        for item in v:
            if not isinstance(item, float) and item != "U":
                raise ValueError("results must be a list of integers or 'U'")
        return v
    
    @property
    def path(self):
        """ Return path to RRD file """
        return "rra_data/" + hashlib.md5((str(self.agent_id) + "-" + str(self.monitor_id)).encode()).hexdigest() + ".rrd"

    def __str__(self):
        """ String representation of rrdHandler object """

        # use pathlib to check if file exists
        if Path(self.path).is_file():
            rrdHandler.rrd_update(self)
            return "RRD file updated"
        else:
            # create directory
            Path("rra_data").mkdir(parents=True, exist_ok=True)
            rrdHandler.rrd_create(self)
            return "RRD file created"

    def rrd_create(self):
        """
        Create RRD file with Kinetic results.
        """

        rrd = []
        rrd.append(self.path)
        rrd.append("--start")
        rrd.append("now-2h")
        rrd.append("--step")
        rrd.append(f"{self.step}")
        rrd.append(f"DS:loss:GAUGE:{self.step*2}:0:{len(self.results)}")
        rrd.append(f"DS:median:GAUGE:{self.step*2}:0:180")
        for i in range(1, len(self.results)+1):
            rrd.append(f"DS:ping{i}:GAUGE:{self.step*2}:0:180")
        rrd.append("RRA:AVERAGE:0.5:1:1008")
        rrd.append("RRA:AVERAGE:0.5:12:4320")
        rrd.append("RRA:MIN:0.5:12:4320")
        rrd.append("RRA:MAX:0.5:12:4320")
        rrd.append("RRA:AVERAGE:0.5:144:720")
        rrd.append("RRA:MAX:0.5:144:720")
        rrd.append("RRA:MIN:0.5:144:720")
        
        # create RRD file
        create(rrd)
        
    def rrd_update(self):
        """
        Update RRD file with Kinetic results.
        """

        rrd = []
        rrd.append(self.path)
        rrd.append("--template")

        rrd_names = "loss:median"

        rrd_loss = len([i for i in self.results if i is None])
        if rrd_loss != len(self.results):
            rrd_median = round(sum([i for i in self.results if i is not None]) / len([i for i in self.results if i is not None]), 3)
        else:
            rrd_median = "NaN"

        rrd_vals = f"N:{rrd_loss}:{rrd_median}"

        for i in range(1, len(self.results)+1):
            rrd_names += f":ping{i}"
            if self.results[i-1] is None:
                rrd_vals += ":NaN"
            else:
                rrd_vals += f":{self.results[i-1]}"

        rrd.append(rrd_names)
        rrd.append(rrd_vals)

        # update RRD file
        update(rrd)

if __name__ == "__main__":
    print("RRD HELPER")
    print(rrdHandler(agent_id=1, monitor_id=1, step=60, results=[5.39, 2.05, 1.18, 12.14, 4.41, 1.16, 3.33, 3.17, 3.63, 3.35, 6.13, 1.67, 6.32, 4.8, 6.8, 4.57, 3.57, 3.14, 3.92, 1.5]))
    print(rrdHandler(agent_id=1, monitor_id=2, step=60, results=[3.56, 4.09, 7.59, 3.17, 3.75]))