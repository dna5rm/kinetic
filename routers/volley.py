"""
Kinetic - Operations for monitor jobs + reporting
"""

from os import path, makedirs
from hashlib import md5
from datetime import datetime, timedelta
from typing import Annotated, Optional, Union
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Agents, Targets, Monitors, Env
from database import SessionLocal
from rrdtool import update, create
from json import loads as json_loads
from humanize import naturaldelta, naturaltime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

router = APIRouter(
    prefix="/volley",
    tags=["volley"],
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

def update_or_create_env_var(env_var, key, value):
    if env_var:
        env_var.value = value
    else:
        return Env(key=key, value=value)

# JobSubmissionModel for submitting job results
class JobSubmissionModel(BaseModel):
    """
    Job submission model

    Input:
    {"id": 1, "results": [7.78, 6.4, 3.88, 3.63, 3.15, 3.66, 2.27, 5.81, 7.19, 3.22, 3.58, 4.79, 0.9, 3.33, 4.16, 0.87, 1.16, 1.13, 3.56, 3.67]}
    {"id": 2, "results": [5.53, 2.66, 5.73, 4.39, 2.65]}

    ID: Monitor job id
    Results: List of latency results
    """
    id: str = Field(..., pattern="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", description="Monitor job id")
    results: list[Union[float, str]] = Field(..., description="List of latency results")

    @field_validator("results")
    def validate_results(cls, v):
        """ Validate results list """
        # length must be between 1 and 35 items
        if len(v) < 1 or len(v) > 35:
            raise ValueError("results must be between 1 and 35 items")
        # each item must be an int or "U"
        for item in v:
            if not isinstance(item, float) and item != "U":
                raise ValueError("results must be a list of floats or 'U'")
        return v

# RRDHandler model for creating/updating RRD files
class RRDHandler(BaseModel):
    """
    Model for creating/updating RRD files.

    Attributes:
        agent_id (str): ID of the agent
        monitor_id (str): ID of the monitor
        step (int): RRD step in seconds
        results (list[int]): List of latency results
    """
    agent_id: str = Field(..., pattern="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", description="Agent id")
    monitor_id: str = Field(..., pattern="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", description="Monitor job id")
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
        rrd_file = "./data/" + md5((str(agent_id) + "-" + str(monitor_id)).encode()).hexdigest() + ".rrd"

        #print(f"agent_id: {agent_id}\nmonitor_id: {monitor_id}\nstep: {step}\nresults: {results}\nrrd_file: {rrd_file}")

        # check if rrd file exists
        if path.exists(rrd_file):
            RRDHandler.rrd_update(agent_id=agent_id, results=results, rrd_file=rrd_file)
        else:
            RRDHandler.rrd_create(agent_id, step=step, results=results, rrd_file=rrd_file)

    def rrd_create(agent_id: int, step: int, results: list[Union[float, str]], rrd_file: str):
        """
        Kinetic - Create RRD file with Kinetic results.

        Args:
            agent_id (str): ID of the agent
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
            agent_id (str): ID of the agent
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

@router.get("/down", include_in_schema=False)
async def down(request: Request, db: DBDependency):
    """ Notification of Down Monitors """

    # Get the value of NOTIFY_HASH database
    NOTIFY_HASH = None
    notify_hash_env = db.query(Env).filter(Env.key == "NOTIFY_HASH").first()
    if notify_hash_env:
        NOTIFY_HASH = notify_hash_env.value

    # Get the value of NOTIFY_HASH database
    NOTIFY_TIME = datetime.now().timestamp()
    notify_time_env = db.query(Env).filter(Env.key == "NOTIFY_TIME").first()
    if notify_time_env:
        NOTIFY_HASH = notify_time_env.value

    # Create context dictionary with app title
    context = {
        "request": request,
        "title": request.app.title,
        "description": request.app.description,
        "server_localtime": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "server_timezone": request.app.server_timezone,
        "server_start_time": request.app.server_start_time,
        "server_run_time": naturaldelta(datetime.now() - request.app.server_start_time)
    }

    # create a flat list of all monitors that both current_loss and prev_loss are both equal to pollcount
    down = [item for sublist in db.query(Monitors.id).filter(Monitors.is_active == True).\
        filter(Monitors.current_loss == Monitors.pollcount).\
        filter(Monitors.prev_loss == Monitors.pollcount).all() for item in sublist]

    # create a hash of the down list
    down_hash = str(hash(str(sorted(down))))
    down_time = datetime.now().timestamp()

    # get all down monitor details
    context["monitors"] = []
    for monitor in down:
        monitor = db.query(Monitors).filter(Monitors.id == monitor).filter(Monitors.is_active == True).first()
        agent = db.query(Agents).filter(Agents.id == monitor.agent_id).filter(Agents.is_active == True).first()
        target = db.query(Targets).filter(Targets.id == monitor.target_id).filter(Targets.is_active == True).first()

        # if down for 2hrs, blue, 5hrs, yellow, 24hrs, red
        if datetime.now() - monitor.last_down > timedelta(hours=12):
            color = "#DC4C64"
        elif datetime.now() - monitor.last_down > timedelta(hours=5):
            color = "#E4A11B"
        elif datetime.now() - monitor.last_down > timedelta(hours=2):
            color = "#54B4D3"

        context["monitors"].append({
            "title": request.app.title,
            "description": request.app.description,
            "agent": agent.name,
            "target": target.address,
            "description": monitor.description,
            "last_down": naturaltime(monitor.last_down),
            "color": color
        })

    # get SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD and NOTIFY_EMAIL from database
    SMTP_SERVER = None
    smtp_server_env = db.query(Env).filter(Env.key == "SMTP_SERVER").first()
    if smtp_server_env:
        SMTP_SERVER = smtp_server_env.value
    SMTP_PORT = None
    smtp_port_env = db.query(Env).filter(Env.key == "SMTP_PORT").first()
    if smtp_port_env:
        SMTP_PORT = smtp_port_env.value
    SMTP_USERNAME = None
    smtp_username_env = db.query(Env).filter(Env.key == "SMTP_USERNAME").first()
    if smtp_username_env:
        SMTP_USERNAME = smtp_username_env.value
    SMTP_PASSWORD = None
    smtp_password_env = db.query(Env).filter(Env.key == "SMTP_PASSWORD").first()
    if smtp_password_env:
        SMTP_PASSWORD = smtp_password_env.value
    NOTIFY_EMAIL = None
    notify_email_env = db.query(Env).filter(Env.key == "NOTIFY_EMAIL").first()
    if notify_email_env:
        NOTIFY_EMAIL = notify_email_env.value

    # if down_hash is not equal to NOTIFY_HASH and down_time is greater than NOTIFY_TIME + 1hr
    if NOTIFY_HASH != down_hash and down_time > float(NOTIFY_TIME) + 3600:

        # update NOTIFY_HASH and NOTIFY_TIME
        NOTIFY_HASH = update_or_create_env_var(NOTIFY_HASH, "NOTIFY_HASH", down_hash)
        NOTIFY_TIME = update_or_create_env_var(NOTIFY_TIME, "NOTIFY_TIME", down_time)
        db.commit()

        # if SMTP_SERVER, SMTP_PORT, SMTP_USERNAME and NOTIFY_EMAIL are set
        if SMTP_SERVER and SMTP_PORT and NOTIFY_EMAIL:

            # Create a MIMEMultipart message object
            message = MIMEMultipart()
            message["From"] = SMTP_USERNAME
            message["To"] = NOTIFY_EMAIL
            message["Subject"] = request.app.title + " - Down Monitor Notification"
            message.attach(MIMEText(templates.get_template("volley_notify.html").render(context), "html"))

            # Create a SMTP session to connect to Gmail's mail server
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()                                                   # Enable secure connection
                if SMTP_USERNAME and SMTP_PASSWORD:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)                      # Login to the sender's email account
                server.sendmail(SMTP_USERNAME, NOTIFY_EMAIL, message.as_string())   # Send the email

    # return email template
    return templates.TemplateResponse("volley_notify.html", context=context)
    #return None

@router.get("/", status_code=status.HTTP_200_OK)
async def volley_script():
    """ Retrun the volley.py script """
    response = PlainTextResponse(open("volley.py", "r").read())
    return response

@router.get("/{agent_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": [{
                        "target_id": "00000000-0000-0000-0000-000000000000",
                        "address": "192.0.2.42",
                        "protocol": "icmp",
                        "port": 0,
                        "dscp": "BE",
                        "pollcount": 20
                    }]
                }
            }
        },
        404: { "content": {
            "application/json": {
                "example": {
                    "detail": "Not Found"
                    }
                }
            }
        }
    }
)
async def read_agent_job(request: Request, db: DBDependency, agent_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Get all monitor jobs by agent id """

    # Get agent address from request
    if request.headers.get('X-Forwarded-For'):
        agent_address = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        agent_address = request.client.host

    # Dont update agent address if localhost
    if agent_address == "127.0.0.1":
        agent_address = None

    # Get agent from database
    agent = db.query(Agents).filter(Agents.id == agent_id).filter(Agents.is_active == True).first()

    # If agent exists
    if agent:
        response = []

        # Update agent address if changed
        if agent_address and agent.address != agent_address:
            agent.address = agent_address
        
        # Update agent last_seen
        agent.last_seen = datetime.now()
        db.commit()

        # Get all monitor jobs by agent id with last_update older than pollinterval
        monitors = db.query(Monitors).filter(Monitors.agent_id == agent_id).filter(Monitors.is_active == True).all()
        monitors = [monitor for monitor in monitors if monitor.last_update < datetime.now() - timedelta(seconds=monitor.pollinterval)]
        
        # Lookup target names by id
        for monitor in monitors:
            target = db.query(Targets).filter(Targets.id == monitor.target_id).filter(Targets.is_active == True).first()

            if target:
                # Append target monitor to the response
                response.append({
                    "id": monitor.id,
                    "address": target.address,
                    "protocol": monitor.protocol,
                    "port": monitor.port,
                    "dscp": monitor.dscp,
                    "pollcount": monitor.pollcount
                })
    else:
        # Agent not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # run down notification
    await down(request, db)

    # Return the response
    return response

@router.put("/{agent_id}", status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: { "content": {
            "application/json": {
                "example": {
                    "status": "success"
                    }
                }
            }
        },
        404: { "content": {
            "application/json": {
                "example": {
                    "detail": "Not Found"
                    }
                }
            }
        }
    }
)
async def update_agent_job(request: Request, db: DBDependency, agent_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Update monitor job by agent id """

    try:
        results = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # load json results
    results = json_loads(results)

    for job in results:

        # validate job input
        try:
            JobSubmissionModel(**job)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        
        job_id = job["id"]
        job_results = job["results"]

        # Get agent address from request
        if request.headers.get('X-Forwarded-For'):
            agent_address = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            agent_address = request.client.host

        # Dont update agent address if localhost
        if agent_address == "127.0.0.1":
            agent_address = None

        # Get agent from database
        agent = db.query(Agents).filter(Agents.id == agent_id).filter(Agents.is_active == True).first()

        # If agent exists
        if agent:
            # Update agent address if changed
            if agent.address != agent_address:
                agent.address = agent_address
            
            # Update agent last_seen
            agent.last_seen = datetime.now()
            db.commit()

            # Get monitor job by id
            monitor = db.query(Monitors).filter(Monitors.id == job_id).filter(Monitors.is_active == True).first()

            # If monitor job exists
            if monitor:
                # Update monitor job results
                latencies = jsonable_encoder(job_results)
                valid = [x for x in latencies if isinstance(x, float)]
                monitor.sample += 1

                # Previous Volley Loss
                monitor.prev_loss = monitor.current_loss

                # Current Volley Stats
                if valid:  # Check if the list is not empty
                    monitor.current_loss = monitor.pollcount - len(valid)
                    monitor.current_median = round(sorted(valid)[len(valid) // 2], 2)
                    monitor.current_min = round(min(valid), 2)
                    monitor.current_max = round(max(valid), 2)
                    monitor.current_stddev = round((sum([((x - monitor.current_median) ** 2) for x in valid]) / len(valid)) ** 0.5, 2)

                    # Aveage Volley Stats
                    monitor.avg_median = round(((monitor.avg_median * (monitor.sample - 1)) + monitor.current_median) / monitor.sample, 2)
                    monitor.avg_min = round(((monitor.avg_min * (monitor.sample - 1)) + monitor.current_min) / monitor.sample, 2)
                    monitor.avg_max = round(((monitor.avg_max * (monitor.sample - 1)) + monitor.current_max) / monitor.sample, 2)
                    monitor.avg_stddev = round(((monitor.avg_stddev * (monitor.sample - 1)) + monitor.current_stddev) / monitor.sample, 2)
                else:
                    monitor.current_loss = monitor.pollcount
                
                # Always update average loss
                monitor.avg_loss = round(((monitor.avg_loss * (monitor.sample - 1)) + monitor.current_loss) / monitor.sample)

                # Update last_down if target goes down from up
                if monitor.current_loss == monitor.pollcount and monitor.prev_loss != monitor.pollcount:
                    monitor.last_down = datetime.now()
                # Update last_down if target goes up from down
                elif monitor.current_loss != monitor.pollcount and monitor.prev_loss == monitor.pollcount:
                    monitor.last_down = datetime.now()

                # Update monitor job last_update
                monitor.last_update = datetime.now()
                monitor.results = jsonable_encoder(job_results)

                # If down add pollinterval to total_down
                if monitor.current_loss == monitor.pollcount:
                    monitor.total_down += monitor.pollinterval

                # Commit changes to database
                db.commit()

                # run RRHandler
                RRDHandler(agent_id=agent.id, monitor_id=monitor.id, step=monitor.pollinterval, results=job_results)

    # Return success
    return { "status": "success" }