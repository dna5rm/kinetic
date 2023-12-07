"""
This script will send a volley of packets to a host and return the average latency and loss
"""

from pydantic import BaseModel, Field, field_validator, IPvAnyAddress, ValidationError
from scapy.all import sr1, IP, IPv6, ICMP, ICMPv6EchoRequest, TCP
from json import dumps as json_dumps, loads as json_loads
import time
import logging                                                                                                    
import requests

# disable scapy warnings
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

class ReadJobInput(BaseModel):
    id: int = Field(ge=1)
    address: str
    protocol: str
    port: int = Field(ge=0, le=65535)
    dscp: str
    pollcount: int = Field(ge=1, le=35)

    @field_validator('address')
    def validate_address(cls, v):
        """ Validate IP address """
        try:
            IPvAnyAddress(v)
        except ValueError as exc:
            raise ValueError('Not a valid Address') from exc
        return v
    
    @field_validator('protocol')
    def validate_protocol(cls, v):
        """ Validate protocol """
        if v.lower() not in ['tcp', 'icmp']:
            raise ValueError("Protocol must be either TCP or ICMP")
        return v.lower()

    @field_validator('dscp')
    def validate_tos(cls, v):
        """ DSCP validation """

        # Define TOS hex mapping of DSCP names
        dscp_name_map = {
            "CS0": 0x00, "BE": 0x00,
            "CS1": 0x20, "AF11": 0x28, "AF12": 0x30, "AF13": 0x38,
            "CS2": 0x40, "AF21": 0x48, "AF22": 0x50, "AF23": 0x58,
            "CS3": 0x60, "AF31": 0x68, "AF32": 0x70, "AF33": 0x78,
            "CS4": 0x80, "AF41": 0x88, "AF42": 0x90, "AF43": 0x98,
            "CS5": 0xA0, "EF": 0xB8,
            "CS6": 0xC0,
            "CS7": 0xE0
        } #dscp_name_map[key]

        # if input is a string, convert to upper case and check if it is in the map
        if isinstance(v, str):
            v = v.upper()
            if v in dscp_name_map:
                return v.upper()
            else:
                raise ValueError("Invalid DSCP, must be one of the following:", list(dscp_name_map.keys()))

class volley(BaseModel):
    ip: str
    protocol: str = "icmp"
    port: int = 0
    volley: int = 5
    dscp: str = 0x00

    @field_validator('ip')
    def validate_ip(cls, v):
        """ Validate IP address """
        try:
            IPvAnyAddress(v)
        except ValueError as exc:
            raise ValueError('Must be a valid IP address') from exc
        return v

    @field_validator('protocol')
    def validate_protocol(cls, v):
        """ Validate protocol """
        if v.lower() not in ['tcp', 'icmp']:
            raise ValueError("Protocol must be either TCP or ICMP")
        return v.lower()

    @field_validator('port')
    def validate_port(cls, v):
        """ Validate port """
        if v < 0 or v > 65535:
            raise ValueError("Port must be a number between 0 and 65535")
        return v

    @field_validator('volley')
    def validate_volley(cls, v):
        """ Validate volley is between 1 to 35 """
        if v < 1 or v > 35:
            raise ValueError("Volley must be between 1 and 35")
        return v

    @field_validator('dscp')
    def validate_tos(cls, v):
        """ Convert to TOS value """

        # Define TOS hex mapping of DSCP names
        dscp_name_map = {
            "CS0": 0x00, "BE": 0x00,
            "CS1": 0x20, "AF11": 0x28, "AF12": 0x30, "AF13": 0x38,
            "CS2": 0x40, "AF21": 0x48, "AF22": 0x50, "AF23": 0x58,
            "CS3": 0x60, "AF31": 0x68, "AF32": 0x70, "AF33": 0x78,
            "CS4": 0x80, "AF41": 0x88, "AF42": 0x90, "AF43": 0x98,
            "CS5": 0xA0, "EF": 0xB8,
            "CS6": 0xC0,
            "CS7": 0xE0
        } #dscp_name_map[key]

        # if input is a string, convert to upper case and check if it is in the map
        if isinstance(v, str):
            v = v.upper()
            if v in dscp_name_map:
                return int(dscp_name_map[v])
            else:
                raise ValueError("Invalid DSCP name provided. Must be one of the following:", list(dscp_name_map.keys()))

    def __str__(self):
        """ Return the string representation of the object """
        result = {}

        if self.protocol == 'icmp':
            # run the ping function and return the results
            latencies = volley.ICMP(self.ip, self.volley, self.dscp)
        
        if self.protocol == 'tcp' and self.port != 0:
            # run the TCP function and return the results
            latencies = volley.TCP(self.ip, self.volley, self.port, self.dscp)
            
        # create a list of all floats in the list
        valid = [x for x in latencies if isinstance(x, float)]

        # add the average to the result if no result then return U
        if valid:
            result['lost'] = self.volley - len(valid)
            result['percent_loss'] = round((result['lost'] / self.volley) * 100)
            result['average'] = round((sum(valid) / len(valid)), 2)
            result['min'] = round(min(valid), 2)
            result['max'] = round(max(valid), 2)
            result['median'] = round(sorted(valid)[len(valid) // 2], 2)
            result['stddev'] = round((sum([((x - result['average']) ** 2) for x in valid]) / len(valid)) ** 0.5, 2)
        else:
            result['total_lost'] = self.volley
            result['percent_loss'] = 100
            result['average'] = "U"
            result['min'] = "U"
            result['max'] = "U"
            result['median'] = "U"
            result['stddev'] = "U"

        # add latency/loss to the result
        result['tos'] = self.dscp
        result['results'] = latencies

        return json_dumps(result, indent=4)

    def ICMP(host, volley=20, tos=0x00):
        """
        Send a volley of ICMP packets to a host and return the average latency and loss
        
        Parameters:
        host (str): Hostname or IP address of the destination
        volley (int): Number of packets to send
        tos (int): TOS value to set on the packet
        """

        latencies = []
        
        if ":" in host:
            packet = IPv6(dst=host, hlim=64, tc=tos)/ICMPv6EchoRequest()
        else:
            packet = IP(dst=host, tos=tos)/ICMP(type=8, code=0)

        # Send the volley of packets
        for i in range(volley):
            # note the time before sending the packet
            start_time = time.time()

            # send the packet and receive the response
            response = sr1(packet, timeout=1, verbose=False)

            # note the time after the packet has been sent
            end_time = time.time()

            # DEBUG: print the response
            #print(response.summary())

            # calculate the difference in time and convert to ms
            if response:
                latency = round((end_time - start_time) * 100, 2)
            else:
                latency = "U"

            # add the latency to the list
            latencies.append(latency)

        return latencies

    def TCP(host, volley=5, port=443, tos=0x00):
        """
        Send a volley of TCP packets to a host and return the average latency and loss
        
        Parameters:
        host (str): Hostname or IP address of the destination
        volley (int): Number of packets to send
        port (int): Port to send the packets to
        tos (int): TOS value to set on the packet
        """

        latencies = []
        packet = IP(dst=host, tos=tos)/TCP(sport=port, dport=port, flags="S")

        # Send the volley of connections
        for i in range(volley):
            # note the time before sending the packet
            start_time = time.time()

            # send the packet and receive the response
            response = sr1(packet, timeout=5, verbose=False)

            # note the time after the packet has been sent
            end_time = time.time()

            # DEBUG: print the response
            #print(response.getlayer(TCP).flags)

            # calculate the difference in time and convert to ms
            if response.getlayer(TCP).flags == "SA":
                latency = round((end_time - start_time) * 100, 2)
            else:
                latency = "U"
            
            # add the latency to the list
            latencies.append(latency)

        return latencies

if __name__ == '__main__':
    #print(volley(ip="172.31.4.129", protocol="tcp", port=22, dscp="EF"))
    #print(volley(ip="172.31.4.129", volley=20, dscp="EF"))

    #print(volley.ICMP("172.31.4.129", 20, 0xE0))
    #print(volley.TCP("172.31.4.129", 5, 22, 0xE0))
    #print(int(0xE0))


    # http request against server
    try:
        jobs = requests.get("http://127.0.0.1:8080/agent/1", headers={"Content-Type": "application/json"})
    except requests.exceptions.ConnectionError as e:
        print("Connection Error:", e)
        quit()

    # loop through each job and print the results
    if jobs:
        for job in jobs.json():

            # validate job against model and quit if invalid
            try:
                ReadJobInput(**job)
            except ValidationError as e:
                print(e.json())
                quit()

            # run a volley against the job and store the results
            data = volley(ip=job['address'], protocol=job['protocol'], port=job['port'], volley=job['pollcount'], dscp=job['dscp'])
            data = json_loads(str(data))
            
            submit = {
                "id": job['id'],
                "results": data['results']
            }

            # send results back to the server as a put request
            try:
                requests.put("http://127.0.0.1:8080/agent/1", headers={"Content-Type": "application/json"}, data=json_dumps(submit))
            except requests.exceptions.ConnectionError as e:
                print("Connection Error:", e)
                quit()

            print(json_dumps(submit))
    else:
        print("No jobs found")