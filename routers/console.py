"""
Kinetic - Server Console
"""

from starlette import status
from starlette.responses import RedirectResponse

from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from models import Agents, Hosts, Monitors
from database import SessionLocal
from datetime import datetime
from humanize import naturaldelta, naturaltime
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass

from pathlib import Path
from random import randint
from re import sub
from hashlib import md5
from base64 import b64encode, decode
from rrdtool import graph
from datetime import datetime, timedelta
import tempfile

router = APIRouter(
    prefix="/console",
    tags=["console"],
    responses={404: {"description": "Not found"}},
    include_in_schema=False
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]
templates = Jinja2Templates(directory="templates")

# Dataclass to report monitor stats
@dataclass
class MonitorStats:
    """ Monitor Stats """

    # Monitor
    id: int
    description: str
    protocol: str
    port: int
    dscp: str

    # HOST
    host_address: str
    host_description: str
    last_change: str
    last_update: str

    # Current
    current_median: float
    current_loss: float

    # Average
    average_median: float
    average_minimum: float
    average_maximum: float
    average_stddev: float
    average_loss: float

    # Color
    current_median_color: str
    current_loss_color: str
    average_median_color: str
    average_minimum_color: str
    average_maximum_color: str
    average_stddev_color: str
    average_loss_color: str

# Class to generate RRD graphs
class RRDGraph:
    def __init__() -> None: pass

    def loss(rrds, polls, step, description, start_time, end_time):
        png_file = tempfile.mktemp(suffix='.png', prefix='rrd_')

        rrd_files = []
    
        # for each agent/monitor
        for rrd_temp in rrds:
            rrd_file = [rrd_temp[0], "rra_data/" + md5((str(rrd_temp[1]) + "-" + str(rrd_temp[2])).encode()).hexdigest() + ".rrd"]
            if Path(rrd_file[1]).is_file():
                rrd_files.append(rrd_file)

        #rrd_files.append("rra_data/" + md5((str(rrds[0]) + "-" + str(rrds[1])).encode()).hexdigest() + ".rrd")

        if rrd_files:
            rrd_graph_str = []

            rrd_graph_str.append("--start")
            rrd_graph_str.append(f"{start_time}")
            rrd_graph_str.append("--end")
            rrd_graph_str.append(f"{end_time}")
            rrd_graph_str.append("--title")
            rrd_graph_str.append(f"{description}")
            rrd_graph_str.append("--height")
            rrd_graph_str.append("55")
            rrd_graph_str.append("--width")
            rrd_graph_str.append("600")
            rrd_graph_str.append("--vertical-label")
            rrd_graph_str.append("Percent")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("BACK#F3F3F3")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("CANVAS#FDFDFD")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("SHADEA#CBCBCB")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("SHADEB#999999")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("FONT#000000")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("AXIS#2C4D43")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("ARROW#2C4D43")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("FRAME#2C4D43")
            rrd_graph_str.append("--border")
            rrd_graph_str.append("1")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("TITLE:10:Arial")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("AXIS:8:Arial")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("LEGEND:9:Courier")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("UNIT:8:Arial")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("WATERMARK:7:Arial")
            rrd_graph_str.append("--imgformat")
            rrd_graph_str.append("PNG")
            rrd_graph_str.append("--rigid")
            rrd_graph_str.append("--upper-limit")
            rrd_graph_str.append("100")
            rrd_graph_str.append("--lower-limit")
            rrd_graph_str.append("0")

            for rrd_idx, rrd_file in enumerate(rrd_files, 0):
                if len(rrd_files) > 1:
                    rrd_color = lambda: randint(0, 255)
                    rrd_color = '#%02X%02X%02X' % (rrd_color(),rrd_color(),rrd_color())
                else:
                    rrd_color = '#FF0000'

                rrd_graph_str.append(f"DEF:loss{rrd_idx}={rrd_file[1]}:loss:LAST")
                rrd_graph_str.append(f"LINE2:loss{rrd_idx}{rrd_color}:{rrd_file[0]}\t")
                rrd_graph_str.append(f"GPRINT:loss{rrd_idx}:LAST:Current Loss\: %5.1lf%%\\j")

            # Done Add footer w/date & time.
            # naturaldelta between start and end epoch times
            timestart = datetime.fromtimestamp(int(start_time)).strftime("%Y-%m-%d")
            timerange = naturaldelta(datetime.fromtimestamp(int(end_time)) - datetime.fromtimestamp(int(start_time)))

            rrd_graph_str.append(f"COMMENT:Date\: {timestart} ({timerange})")
            rrd_graph_str.append(f"COMMENT:Probe\: {polls}x/{step}sec interval\\j")

            #print("### rrd_graph_str ###\n", rrd_graph_str)
            
            graph(png_file, rrd_graph_str)
            png_output = "data:image/png;base64, "
            with open(png_file, "rb") as image_file:
                png_output += b64encode(image_file.read()).decode('UTF-8')
            Path(png_file).unlink()
            
            return png_output

    def smoke(rrds, polls, step, description, start_time, end_time):
        png_file = tempfile.mktemp(suffix='.png', prefix='rrd_')

        rrd_files = []
    
        # for each agent/monitor
        for rrd_temp in rrds:
            rrd_file = [rrd_temp[0], "rra_data/" + md5((str(rrd_temp[1]) + "-" + str(rrd_temp[2])).encode()).hexdigest() + ".rrd"]
            if Path(rrd_file[1]).is_file():
                rrd_files.append(rrd_file)

        #rrd_files.append("rra_data/" + md5((str(rrds[0]) + "-" + str(rrds[1])).encode()).hexdigest() + ".rrd")

        if rrd_files:
            rrd_graph_str = []

            rrd_graph_str.append("--start")
            rrd_graph_str.append(f"{start_time}")
            rrd_graph_str.append("--end")
            rrd_graph_str.append(f"{end_time}")
            rrd_graph_str.append("--title")
            rrd_graph_str.append(f"{description}")
            rrd_graph_str.append("--height")
            rrd_graph_str.append("95")
            rrd_graph_str.append("--width")
            rrd_graph_str.append("600")
            rrd_graph_str.append("--vertical-label")
            rrd_graph_str.append("Milliseconds")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("BACK#F3F3F3")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("CANVAS#FDFDFD")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("SHADEA#CBCBCB")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("SHADEB#999999")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("FONT#000000")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("AXIS#2C4D43")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("ARROW#2C4D43")
            rrd_graph_str.append("--color")
            rrd_graph_str.append("FRAME#2C4D43")
            rrd_graph_str.append("--border")
            rrd_graph_str.append("1")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("TITLE:10:Arial")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("AXIS:8:Arial")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("LEGEND:9:Courier")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("UNIT:8:Arial")
            rrd_graph_str.append("--font")
            rrd_graph_str.append("WATERMARK:7:Arial")
            rrd_graph_str.append("--imgformat")
            rrd_graph_str.append("PNG")
            rrd_graph_str.append("--rigid")

            for rrd_idx, rrd_file in enumerate(rrd_files, 0):
                if len(rrd_files) > 1:
                    rrd_color = lambda: randint(0, 255)
                    rrd_color = '#%02X%02X%02X' % (rrd_color(),rrd_color(),rrd_color())
                else:
                    rrd_color = '#FF0000'

                rrd_graph_str.append(f"DEF:median{rrd_idx}={rrd_file[1]}:median:AVERAGE")
                rrd_graph_str.append(f"DEF:loss{rrd_idx}={rrd_file[1]}:loss:AVERAGE")
                for result_num in range(1, polls+1):
                    rrd_graph_str.append(f"DEF:result{rrd_idx}p{result_num}={rrd_file[1]}:result{result_num}:AVERAGE")

                rrd_graph_str.append(f"CDEF:ploss{rrd_idx}=loss{rrd_idx},20,/,100,*")
                rrd_graph_str.append(f"CDEF:dm{rrd_idx}=median{rrd_idx},0,100000,LIMIT")
                for result_num in range(1, polls+1):
                    rrd_graph_str.append(f"CDEF:p{rrd_idx}p{result_num}=result{rrd_idx}p{result_num},UN,0,result{rrd_idx}p{result_num},IF")

                temp_str = f"CDEF:results{rrd_idx}={polls},p{rrd_idx}p1,UN"
                for result_num in range(2, polls+1):
                    temp_str += f",p{rrd_idx}p{result_num},UN,+"
                temp_str += ",-"
                rrd_graph_str.append(temp_str)
                temp_str = None

                temp_str = f"CDEF:m{rrd_idx}=p{rrd_idx}p1"
                for result_num in range(2, polls+1):
                    temp_str += f",p{rrd_idx}p{result_num},+"
                temp_str += f",results{rrd_idx},/"
                rrd_graph_str.append(temp_str)
                temp_str = None

                temp_str = f"CDEF:sdev{rrd_idx}=p{rrd_idx}p1,m{rrd_idx},-,DUP,*"
                for result_num in range(2, polls+1):
                    temp_str += f",p{rrd_idx}p{result_num},m{rrd_idx},-,DUP,*,+"
                temp_str += f",results{rrd_idx},/,SQRT"
                rrd_graph_str.append(temp_str)
                temp_str = None

                rrd_graph_str.append(f"CDEF:dmlow{rrd_idx}=dm{rrd_idx},sdev{rrd_idx},2,/,-")
                rrd_graph_str.append(f"CDEF:s2d{rrd_idx}=sdev{rrd_idx}")
                rrd_graph_str.append(f"AREA:dmlow{rrd_idx}")
                rrd_graph_str.append(f"AREA:s2d{rrd_idx}{rrd_color}30:STACK")
                rrd_graph_str.append(f"LINE2:dm{rrd_idx}{rrd_color}:{rrd_file[0]}\t")
                rrd_graph_str.append(f"VDEF:avmed{rrd_idx}=median{rrd_idx},AVERAGE")
                rrd_graph_str.append(f"VDEF:avsd{rrd_idx}=sdev{rrd_idx},AVERAGE")
                rrd_graph_str.append(f"CDEF:msr{rrd_idx}=median{rrd_idx},POP,avmed{rrd_idx},avsd{rrd_idx},/")
                rrd_graph_str.append(f"VDEF:avmsr{rrd_idx}=msr{rrd_idx},AVERAGE")
                rrd_graph_str.append(f"GPRINT:avmed{rrd_idx}:Median RTT\: %5.2lfms")
                rrd_graph_str.append(f"GPRINT:ploss{rrd_idx}:AVERAGE:Loss\: %5.1lf%%")
                rrd_graph_str.append(f"GPRINT:avsd{rrd_idx}:Std Dev\: %5.2lfms")
                rrd_graph_str.append(f"GPRINT:avmsr{rrd_idx}:Ratio\: %5.1lfms\\j")

            # Done Add footer w/date & time.
            # naturaldelta between start and end epoch times
            timestart = datetime.fromtimestamp(int(start_time)).strftime("%Y-%m-%d")
            timerange = naturaldelta(datetime.fromtimestamp(int(end_time)) - datetime.fromtimestamp(int(start_time)))

            rrd_graph_str.append(f"COMMENT:Date\: {timestart} ({timerange})")
            rrd_graph_str.append(f"COMMENT:Probe\: {polls}x/{step}sec interval\\j")

            #print("### rrd_graph_str ###\n", rrd_graph_str)
            
            graph(png_file, rrd_graph_str)
            png_output = "data:image/png;base64, "
            with open(png_file, "rb") as image_file:
                png_output += b64encode(image_file.read()).decode('UTF-8')
            Path(png_file).unlink()
            
            return png_output

# StatReport Function: console_agent and console_search
def StatReport(db: DBDependency, monitors):
    """ Stat Report Page """

    context = {}
    monitor_stats = []

    # for each monitor
    for monitor in monitors:
        
        # lookup monitor in the monitor table
        monitor = db.query(Monitors).filter(Monitors.id == monitor).first()

        # lookup agent_id and host_id
        agent = db.query(Agents).filter(Agents.id == monitor.agent_id).first()
        host = db.query(Hosts).filter(Hosts.id == monitor.host_id).first()

        # if agent and host exists and both are active
        if agent and agent.is_active and host and host.is_active:

            # get pollcount from monitor
            pollcount = monitor.pollcount

            # get last update times from monitor and convert to naturaldelta
            # remove the word "ago" from the string
            last_change = naturaltime(monitor.last_change).replace(" ago", "")
            last_update = naturaltime(monitor.last_update)

            # get current stats from monitor
            current_median = monitor.current_median
            current_min = monitor.current_min
            current_max = monitor.current_max
            current_stddev = monitor.current_stddev
            current_loss = int((monitor.current_loss / pollcount) * 100)

            # threshold based on stddev of min and max.
            # If stddev is greater than 10% of the difference between min and max, then the monitor is considered unstable
            current_median_threshold = (current_max - current_min) * 0.10

            if current_stddev > current_median_threshold:
                current_median_color = "bg-warning"
            elif current_median > current_max:
                current_median_color = "bg-danger"
            else:
                current_median_color = "bg-success"
                
            # current loss threshold
            if current_loss > 10:
                current_loss_color = "bg-warning"
            elif current_loss > 20:
                current_loss_color = "bg-danger"
            else:
                current_loss_color = "bg-success"

            # get average stats from monitor
            average_median = monitor.avg_median
            average_minimum = monitor.avg_min
            average_maximum = monitor.avg_max
            average_stddev = monitor.avg_stddev
            average_loss = int((monitor.avg_loss / pollcount) * 100)

            # threshold based on stddev of min and max.
            # If stddev is greater than 10% of the difference between min and max, then the monitor is considered unstable
            average_median_threshold = (average_maximum - average_minimum) * 0.10

            if average_stddev > average_median_threshold:
                average_median_color = "bg-warning"
            elif average_median > average_maximum:
                average_median_color = "bg-danger"
            else:
                average_median_color = "bg-success"

            average_minimum_threshold = (average_maximum - average_minimum) * 0.10

            if average_minimum < average_minimum_threshold:
                average_minimum_color = "bg-warning"
            elif average_minimum > average_maximum:
                average_minimum_color = "bg-danger"
            else:
                average_minimum_color = "bg-success"
                
            average_maximum_threshold = (average_maximum - average_minimum) * 0.10
                
            if average_maximum > average_maximum_threshold:
                average_maximum_color = "bg-warning"
            elif average_maximum < average_minimum:
                average_maximum_color = "bg-danger"
            else:
                average_maximum_color = "bg-success"

            average_stddev_threshold = (average_maximum - average_minimum) * 0.10
                
            if average_stddev > average_stddev_threshold:
                average_stddev_color = "bg-warning"
            elif average_stddev > average_maximum:
                average_stddev_color = "bg-danger"
            else:
                average_stddev_color = "bg-success"

            # average loss threshold
            if average_loss > 10:
                average_loss_color = "bg-warning"
            elif average_loss > 20:
                average_loss_color = "bg-danger"
            else:
                average_loss_color = "bg-success"

            # create a MonitorStats object of the monitor
            monitor_stats.append(MonitorStats(
                id=monitor.id,
                description=monitor.description,
                protocol=monitor.protocol,
                port=monitor.port,
                dscp=monitor.dscp,
                host_description=host.description,
                host_address=host.address,
                last_change=last_change,
                current_median=current_median,
                current_loss=current_loss,
                average_median=average_median,
                average_minimum=average_minimum,
                average_maximum=average_maximum,
                average_stddev=average_stddev,
                average_loss=average_loss,
                last_update=last_update,
                current_median_color=current_median_color,
                current_loss_color=current_loss_color,
                average_median_color=average_median_color,
                average_minimum_color=average_minimum_color,
                average_maximum_color=average_maximum_color,
                average_stddev_color=average_stddev_color,
                average_loss_color=average_loss_color
            ))

            # append to context
            context.update({
                "stats": monitor_stats
            })

    return context

@router.get("/", response_class=HTMLResponse)
async def console_home(request: Request, db: DBDependency):
    """ Console - Home """

    # get a list of all agents where is_active is True
    agents = db.query(Agents).filter(Agents.is_active == True).all()

    # Create context dictionary with app title
    context = {
        "request": request,
        "title": request.app.title,
        "description": request.app.description,
        "agents": agents,
        "stats": {
            "active_agents": len(agents),
            "active_hosts": db.query(Hosts).filter(Hosts.is_active == True).count(),
            "active_monitors": db.query(Monitors).filter(Monitors.is_active == True).count(),
            "total_agents": db.query(Agents).count(),
            "total_hosts": db.query(Hosts).count(),
            "total_monitors": db.query(Monitors).count(),
            "server_start_time": request.app.server_start_time,
            "server_run_time": naturaldelta(datetime.now() - request.app.server_start_time)
        }
    }

    # Include the app title in response.
    return templates.TemplateResponse("home.html", context=context)

@router.get("/agent/{agent_id}", response_class=HTMLResponse)
# get agent_id from path and pass it to console_agent
async def console_agent(request: Request, agent_id: int, db: DBDependency):
    """ Console - Monitors by Agent """

    # get agent from database by agent_id
    agent = db.query(Agents).filter(Agents.id == agent_id).first()

    # if agent esists and is active
    if agent and agent.is_active:

        # create a flat list of all monitors where agent_id is equal to agent.id
        monitor_match = [item for sublist in db.query(Monitors.id).filter(Monitors.agent_id == agent.id).all() for item in sublist]

        # Create context dictionary with agent data
        context = {
            "request": request,
            "title": request.app.title,
            "description": request.app.description,
            "agent": agent
        }

        # append StatReport to context
        context.update(StatReport(db, monitor_match))

    return templates.TemplateResponse("stats.html", context=context)

@router.get("/host/{host_id}", response_class=HTMLResponse)
async def console_host(request: Request, host_id: int, db: DBDependency):
    # Default raise HTTPException with 404 status code
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"host_id not found")

@router.get("/monitor/{monitor_id}", response_class=HTMLResponse)
async def console_monitor(request: Request, monitor_id: int, db: DBDependency):
    """ Console - Monitor Graphs """
    # get monitor from database by monitor_id
    monitor = db.query(Monitors).filter(Monitors.id == monitor_id).first()

    # if monitor exists and is active
    if monitor and monitor.is_active:

        # get host from database by host_id
        host = db.query(Hosts).filter(Hosts.id == monitor.host_id).first()

        # get agent from database by agent_id
        agent = db.query(Agents).filter(Agents.id == monitor.agent_id).first()

        # if host and agent exists and is active
        if host and host.is_active and agent and agent.is_active:

            # get start and end times from query parameters
            rrd_start = request.query_params.get("start")
            rrd_end = request.query_params.get("end")

            # if start and end times are not specified, default to 1 hour
            if not rrd_start or not rrd_end:
                rrd_start = (datetime.now()-timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
                rrd_end = datetime.now().strftime("%Y-%m-%dT%H:%M")

            rrds = []
            rrds.append([host.address, agent.id, monitor.id])

            # Create context dictionary with monitor data
            context = {
                "request": request,
                "title": request.app.title,
                "description": request.app.description,
                "agent": agent,
                "host": host,
                "monitor": monitor,
                "start": rrd_start,
                "end": rrd_end,
                "timezone": request.app.server_timezone,
                "graph": {
                    "smoke": RRDGraph.smoke(rrds,
                                        monitor.pollcount,
                                        monitor.pollinterval,
                                        f"{agent.name}: {monitor.description}",
                                        datetime.strptime(rrd_start, '%Y-%m-%dT%H:%M').strftime("%s"),
                                        datetime.strptime(rrd_end, '%Y-%m-%dT%H:%M').strftime("%s")),
                    "loss": RRDGraph.loss(rrds,
                                        monitor.pollcount,
                                        monitor.pollinterval,
                                        f"{agent.name}: {monitor.description}",
                                        datetime.strptime(rrd_start, '%Y-%m-%dT%H:%M').strftime("%s"),
                                        datetime.strptime(rrd_end, '%Y-%m-%dT%H:%M').strftime("%s"))
                }
            }

            return templates.TemplateResponse("monitor.html", context=context)

    # Default raise HTTPException with 404 status code
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"monitor_id not found")

@router.get("/search", response_class=HTMLResponse)
async def console_search(request: Request, db: DBDependency):
    """ Console - Search monitors by host, agent or monitor description """

    # get search query from query parameters
    search = request.query_params.get("query")

    # if search query is not specified, default to empty string
    if search:
        
        monitors = []

        # check Agent table name, address, description columns for search query and add its id to agent_match list
        agent_match = db.query(Agents.id).filter(Agents.name.like(f"%{search}%")).\
            union_all(db.query(Agents.id).filter(Agents.address.like(f"%{search}%"))).\
            union_all(db.query(Agents.id).filter(Agents.description.like(f"%{search}%"))).\
            all()

        host_match = db.query(Hosts.id).filter(Hosts.address.like(f"%{search}%")).\
            union_all(db.query(Hosts.id).filter(Hosts.description.like(f"%{search}%"))).\
            all()

        # flatten list of lists
        agent_match = list(set([item for sublist in agent_match for item in sublist]))
        host_match = list(set([item for sublist in host_match for item in sublist]))

        # search for monitor_id where host_id or agent_id exists in agent_match or host_match or were found in description
        monitor_match = db.query(Monitors.id).filter(Monitors.agent_id.in_(agent_match)).\
            union_all(db.query(Monitors.id).filter(Monitors.host_id.in_(host_match))).\
            union_all(db.query(Monitors.id).filter(Monitors.description.like(f"%{search}%"))).\
            all()
        
        # flatten list of lists
        monitor_match = list(set([item for sublist in monitor_match for item in sublist]))

        # call StatReport to get monitor stats
        context = {
            "request": request,
            "title": request.app.title,
            "description": request.app.description,
        }

        # append StatReport to context
        context.update(StatReport(db, monitor_match))
        return templates.TemplateResponse("stats.html", context=context)

    return RedirectResponse(url="/console", status_code=status.HTTP_302_FOUND)