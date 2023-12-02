#!/bin/env python3

"""
RRDTool helper functions.
"""

from pathlib import Path
from statistics import median
from base64 import b64encode, decode
from datetime import datetime
from random import randint
from re import sub
import rrdtool
import tempfile
import timeago
#from pprint import pprint

RRA_PREFIX = "fping/rra"

def rrd_fping (rrd_agent, rrd_host, rrd_result):
    """
    Create & Update RRD file with fping results.
    """

    rrd_file = f"{RRA_PREFIX}/{rrd_agent}_{rrd_host}.rrd"

    rrd_step = 300 # 5min
    rrd_pings = len(rrd_result)

    if Path(rrd_file).is_file():
        rrd_update_str = []
        rrd_update_str.append(rrd_file)
        rrd_update_str.append("--template")

        rrd_names = "loss:median"

        fping_loss = len([i for i in rrd_result if i is None])
        if fping_loss != len(rrd_result):
            fping_median = round(median([i for i in rrd_result if i is not None]), 3)
        else:
            fping_median = "NaN"

        rrd_vals = f"N:{fping_loss}:{fping_median}"

        for i in range(1, rrd_pings+1):
            rrd_names += f":ping{i}"
            if rrd_result[i-1] is None:
                rrd_vals += ":NaN"
            else:
                rrd_vals += f":{rrd_result[i-1]}"

        rrd_update_str.append(rrd_names)
        rrd_update_str.append(rrd_vals)

        #print(rrd_update_str)
        rrdtool.update(rrd_update_str)

    else:
        Path(RRA_PREFIX).mkdir(parents=True, exist_ok=True)

        rrd_create_str = []
        rrd_create_str.append(rrd_file)
        rrd_create_str.append("--start")
        rrd_create_str.append("now-2h")
        rrd_create_str.append("--step")
        rrd_create_str.append(f"{rrd_step}")
        rrd_create_str.append(f"DS:loss:GAUGE:{rrd_step*2}:0:{rrd_pings}")
        rrd_create_str.append(f"DS:median:GAUGE:{rrd_step*2}:0:180")
        for ping_num in range(1, rrd_pings+1):
            rrd_create_str.append(f"DS:ping{ping_num}:GAUGE:{rrd_step*2}:0:180")
        rrd_create_str.append("RRA:AVERAGE:0.5:1:1008")
        rrd_create_str.append("RRA:AVERAGE:0.5:12:4320")
        rrd_create_str.append("RRA:MIN:0.5:12:4320")
        rrd_create_str.append("RRA:MAX:0.5:12:4320")
        rrd_create_str.append("RRA:AVERAGE:0.5:144:720")
        rrd_create_str.append("RRA:MAX:0.5:144:720")
        rrd_create_str.append("RRA:MIN:0.5:144:720")

        #print(rrd_create_str)
        rrdtool.create(rrd_create_str)

class rrd_graph:
    def __init__():
        pass

    def multi (rrds, rrd_start, rrd_end):

        rrd_pings = 20
        rrd_step = 300

        png_file = tempfile.mktemp(suffix='.png', prefix='rrd_')
        rrd_files = []

        rand_hex = lambda: randint(0,255)
        rrd_address = rrds[0][1]
        rrd_hostname = rrds[0][2]
        rrd_date = datetime.fromtimestamp(int(rrd_end)).strftime('%A %d %B %Y %H\:%M UTC')
        rrd_timeago = sub('^in ', '', timeago.format(int(rrd_end), int(rrd_start)))

        for rrd_temp in rrds:
            rrd_file = f"{RRA_PREFIX}/{rrd_temp[0]}_{rrd_temp[1]}.rrd"
            if Path(rrd_file).is_file():
                rrd_files.append(rrd_file)

        if len(rrd_files) > 1:
            rrd_graph_str = []

            rrd_graph_str.append("--start")
            rrd_graph_str.append(f"{rrd_start}")
            rrd_graph_str.append("--end")
            rrd_graph_str.append(f"{rrd_end}")
            rrd_graph_str.append("--title")
            rrd_graph_str.append(f"{rrd_hostname} - {rrd_address}")
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

            for rrd_idx, rrd_file in enumerate(rrd_files, 0):
                rrd_agent = rrds[rrd_idx][0]
                rrd_color = '#%02X%02X%02X' % (rand_hex(),rand_hex(),rand_hex())

                rrd_graph_str.append(f"DEF:median{rrd_idx}={rrd_file}:median:AVERAGE")
                rrd_graph_str.append(f"DEF:loss{rrd_idx}={rrd_file}:loss:AVERAGE")
                for ping_num in range(1, rrd_pings+1):
                    rrd_graph_str.append(f"DEF:ping{rrd_idx}p{ping_num}={rrd_file}:ping{ping_num}:AVERAGE")

                rrd_graph_str.append(f"CDEF:ploss{rrd_idx}=loss{rrd_idx},20,/,100,*")
                rrd_graph_str.append(f"CDEF:dm{rrd_idx}=median{rrd_idx},0,100000,LIMIT")
                for ping_num in range(1, rrd_pings+1):
                    rrd_graph_str.append(f"CDEF:p{rrd_idx}p{ping_num}=ping{rrd_idx}p{ping_num},UN,0,ping{rrd_idx}p{ping_num},IF")

                temp_str = f"CDEF:pings{rrd_idx}={rrd_pings},p{rrd_idx}p1,UN"
                for ping_num in range(2, rrd_pings+1):
                    temp_str += f",p{rrd_idx}p{ping_num},UN,+"
                temp_str += ",-"
                rrd_graph_str.append(temp_str)
                temp_str = None

                temp_str = f"CDEF:m{rrd_idx}=p{rrd_idx}p1"
                for ping_num in range(2, rrd_pings+1):
                    temp_str += f",p{rrd_idx}p{ping_num},+"
                temp_str += f",pings{rrd_idx},/"
                rrd_graph_str.append(temp_str)
                temp_str = None

                temp_str = f"CDEF:sdev{rrd_idx}=p{rrd_idx}p1,m{rrd_idx},-,DUP,*"
                for ping_num in range(2, rrd_pings+1):
                    temp_str += f",p{rrd_idx}p{ping_num},m{rrd_idx},-,DUP,*,+"
                temp_str += f",pings{rrd_idx},/,SQRT"
                rrd_graph_str.append(temp_str)
                temp_str = None

                rrd_graph_str.append(f"CDEF:dmlow{rrd_idx}=dm{rrd_idx},sdev{rrd_idx},2,/,-")
                rrd_graph_str.append(f"CDEF:s2d{rrd_idx}=sdev{rrd_idx}")
                rrd_graph_str.append(f"AREA:dmlow{rrd_idx}")
                rrd_graph_str.append(f"AREA:s2d{rrd_idx}{rrd_color}30:STACK")
                rrd_graph_str.append(f"LINE1:dm{rrd_idx}{rrd_color}:{rrd_agent}\t")
                rrd_graph_str.append(f"VDEF:avmed{rrd_idx}=median{rrd_idx},AVERAGE")
                rrd_graph_str.append(f"VDEF:avsd{rrd_idx}=sdev{rrd_idx},AVERAGE")
                rrd_graph_str.append(f"CDEF:msr{rrd_idx}=median{rrd_idx},POP,avmed{rrd_idx},avsd{rrd_idx},/")
                rrd_graph_str.append(f"VDEF:avmsr{rrd_idx}=msr{rrd_idx},AVERAGE")
                rrd_graph_str.append(f"GPRINT:avmed{rrd_idx}:Median RTT\: %5.2lfms")
                rrd_graph_str.append(f"GPRINT:ploss{rrd_idx}:AVERAGE:Loss\: %5.1lf%%")
                rrd_graph_str.append(f"GPRINT:avsd{rrd_idx}:Std Dev\: %5.2lfms")
                rrd_graph_str.append(f"GPRINT:avmsr{rrd_idx}:Ratio\: %5.1lfms\\j")

            # Done Add footer w/date & time.
            rrd_graph_str.append(f"COMMENT:Probe\: {rrd_pings} pings every {rrd_step} seconds")
            rrd_graph_str.append(f"COMMENT:{rrd_date} ({rrd_timeago})\\j")

            # print("### rrd_graph_str ###\n", rrd_graph_str)
            
            rrdtool.graph(png_file, rrd_graph_str)
            png_output = "data:image/png;base64, "
            with open(png_file, "rb") as image_file:
                png_output += b64encode(image_file.read()).decode('UTF-8')
            Path(png_file).unlink()
            
            return png_output
        else:
            return None

    def smoke (rrds, rrd_start, rrd_end):
        """
        Generate a PNG from fping rrd.
        """

        rrd_idx = 0
        rrd_pings = 20
        rrd_step = 300
        rrd_color = ( "0F0f00", "00FF00", "00BBFF", "0022FF", "8A2BE2", "FA0BE2", "C71585", "FF0000" )
        rrd_line = .5

        rrd_agent = rrds[0]
        rrd_address = rrds[1]
        rrd_hostname = rrds[2]

        rrd_date = datetime.fromtimestamp(int(rrd_end)).strftime('%A %d %B %Y %H\:%M UTC')
        rrd_timeago = sub('^in ', '', timeago.format(int(rrd_end), int(rrd_start)))
        rrd_file = f"{RRA_PREFIX}/{rrd_agent}_{rrd_address}.rrd"
        png_file = tempfile.mktemp(suffix='.png', prefix='rrd_')

        if Path(rrd_file).is_file():
            rrd_graph_str = []
            rrd_graph_str.append("--start")
            rrd_graph_str.append(f"{rrd_start}")
            rrd_graph_str.append("--end")
            rrd_graph_str.append(f"{rrd_end}")
            rrd_graph_str.append("--title")
            rrd_graph_str.append(f"{rrd_agent}: {rrd_hostname} - {rrd_address}")
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

            rrd_graph_str.append(f"DEF:median{rrd_idx}={rrd_file}:median:AVERAGE")
            rrd_graph_str.append(f"DEF:loss{rrd_idx}={rrd_file}:loss:AVERAGE")
            for ping_num in range(1, rrd_pings+1):
                rrd_graph_str.append(f"DEF:ping{rrd_idx}p{ping_num}={rrd_file}:ping{ping_num}:AVERAGE")

            rrd_graph_str.append(f"CDEF:ploss{rrd_idx}=loss{rrd_idx},20,/,100,*")
            rrd_graph_str.append(f"CDEF:dm{rrd_idx}=median{rrd_idx},0,100000,LIMIT")
            for ping_num in range(1, rrd_pings+1):
                rrd_graph_str.append(f"CDEF:p{rrd_idx}p{ping_num}=ping{rrd_idx}p{ping_num},UN,0,ping{rrd_idx}p{ping_num},IF")

            temp_str = f"CDEF:pings{rrd_idx}={rrd_pings},p{rrd_idx}p1,UN"
            for ping_num in range(2, rrd_pings+1):
                temp_str += f",p{rrd_idx}p{ping_num},UN,+"
            temp_str += ",-"
            rrd_graph_str.append(temp_str)
            temp_str = None

            temp_str = f"CDEF:m{rrd_idx}=p{rrd_idx}p1"
            for ping_num in range(2, rrd_pings+1):
                temp_str += f",p{rrd_idx}p{ping_num},+"
            temp_str += f",pings{rrd_idx},/"
            rrd_graph_str.append(temp_str)
            temp_str = None

            temp_str = f"CDEF:sdev{rrd_idx}=p{rrd_idx}p1,m{rrd_idx},-,DUP,*"
            for ping_num in range(2, rrd_pings+1):
                temp_str += f",p{rrd_idx}p{ping_num},m{rrd_idx},-,DUP,*,+"
            temp_str += f",pings{rrd_idx},/,SQRT"
            rrd_graph_str.append(temp_str)
            temp_str = None

            rrd_graph_str.append(f"CDEF:dmlow{rrd_idx}=dm{rrd_idx},sdev{rrd_idx},2,/,-")
            rrd_graph_str.append(f"CDEF:s2d{rrd_idx}=sdev{rrd_idx}")
            rrd_graph_str.append(f"AREA:dmlow{rrd_idx}")
            rrd_graph_str.append(f"AREA:s2d{rrd_idx}#{rrd_color[0]}30:STACK")

            rrd_graph_str.append(f"VDEF:avmed{rrd_idx}=median{rrd_idx},AVERAGE")
            rrd_graph_str.append(f"VDEF:avsd{rrd_idx}=sdev{rrd_idx},AVERAGE")
            rrd_graph_str.append(f"CDEF:msr{rrd_idx}=median{rrd_idx},POP,avmed{rrd_idx},avsd{rrd_idx},/")
            rrd_graph_str.append(f"VDEF:avmsr{rrd_idx}=msr{rrd_idx},AVERAGE")
            rrd_graph_str.append(f"LINE3:avmed{rrd_idx}#{rrd_color[1]}25:")

            # Header Output
            rrd_graph_str.append("COMMENT:\t\t")
            rrd_graph_str.append("COMMENT:Average")
            rrd_graph_str.append("COMMENT:Maximum")
            rrd_graph_str.append("COMMENT:Minimum")
            rrd_graph_str.append("COMMENT:Current")
            rrd_graph_str.append("COMMENT:Std Dev")
            rrd_graph_str.append("COMMENT: \\j")

            # RTT Data Output
            rrd_graph_str.append("COMMENT:Median RTT\: \t")
            rrd_graph_str.append(f"GPRINT:avmed{rrd_idx}:%.2lf")
            rrd_graph_str.append(f"GPRINT:median{rrd_idx}:MAX:%.2lf")
            rrd_graph_str.append(f"GPRINT:median{rrd_idx}:MIN:%.2lf")
            rrd_graph_str.append(f"GPRINT:median{rrd_idx}:LAST:%.2lf")
            rrd_graph_str.append(f"GPRINT:avsd{rrd_idx}:%.2lf")
            rrd_graph_str.append("COMMENT: \\j")

            # Loss Data Output
            rrd_graph_str.append("COMMENT:Packet Loss\:\t")
            rrd_graph_str.append(f"GPRINT:ploss{rrd_idx}:AVERAGE:%.2lf%%")
            rrd_graph_str.append(f"GPRINT:ploss{rrd_idx}:MAX:%.2lf%%")
            rrd_graph_str.append(f"GPRINT:ploss{rrd_idx}:MIN:%.2lf%%")
            rrd_graph_str.append(f"GPRINT:ploss{rrd_idx}:LAST:%.2lf%%")
            rrd_graph_str.append("COMMENT:  -  ")
            rrd_graph_str.append("COMMENT: \\j")

            # Colored Median Line
            rrd_graph_str.append("COMMENT:Loss Colors\:\t")
            rrd_graph_str.append(f"CDEF:me0=loss{rrd_idx},-1,GT,loss{rrd_idx},0,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL0=me0,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH0=me0,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL0")
            rrd_graph_str.append(f"STACK:meH0#{rrd_color[1]}: 0/{rrd_pings}")

            rrd_graph_str.append(f"CDEF:me1=loss{rrd_idx},0,GT,loss{rrd_idx},1,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL1=me1,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH1=me1,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL1")
            rrd_graph_str.append(f"STACK:meH1#{rrd_color[2]}: 1/{rrd_pings}")

            rrd_graph_str.append(f"CDEF:me2=loss{rrd_idx},1,GT,loss{rrd_idx},2,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL2=me2,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH2=me2,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL2")
            rrd_graph_str.append(f"STACK:meH2#{rrd_color[3]}: 2/{rrd_pings}")

            rrd_graph_str.append(f"CDEF:me3=loss{rrd_idx},2,GT,loss{rrd_idx},3,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL3=me3,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH3=me3,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL3")
            rrd_graph_str.append(f"STACK:meH3#{rrd_color[4]}: 3/{rrd_pings}")

            rrd_graph_str.append(f"CDEF:me4=loss{rrd_idx},3,GT,loss{rrd_idx},4,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL4=me4,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH4=me4,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL4")
            rrd_graph_str.append(f"STACK:meH4#{rrd_color[5]}: 4/{rrd_pings}")

            rrd_graph_str.append(f"CDEF:me10=loss{rrd_idx},4,GT,loss{rrd_idx},10,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL10=me10,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH10=me10,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL10")
            rrd_graph_str.append(f"STACK:meH10#{rrd_color[6]}: 10/{rrd_pings}")

            rrd_graph_str.append(f"CDEF:me19=loss{rrd_idx},10,GT,loss{rrd_idx},19,LE,*,1,UNKN,IF,median{rrd_idx},*")
            rrd_graph_str.append(f"CDEF:meL19=me19,{rrd_line},-")
            rrd_graph_str.append(f"CDEF:meH19=me19,0,*,{rrd_line},2,*,+")
            rrd_graph_str.append("AREA:meL19")
            rrd_graph_str.append(f"STACK:meH19#{rrd_color[7]}: 19/{rrd_pings}\\j")

            # Solid Median Line
            # rrd_graph_str.append(f"LINE1:median{rrd_idx}#{rrd_color[0]}75:")

            rrd_graph_str.append(f"COMMENT:Probe\: {rrd_pings} pings every {rrd_step} seconds")
            rrd_graph_str.append(f"COMMENT:{rrd_date} ({rrd_timeago})\\j")

            # print("### rrd_graph_str ###\n", rrd_graph_str)
            
            rrdtool.graph(png_file, rrd_graph_str)
            png_output = "data:image/png;base64, "
            with open(png_file, "rb") as image_file:
                png_output += b64encode(image_file.read()).decode('UTF-8')
            Path(png_file).unlink()
            
        else:
            png_output = " data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAArkAAADtCAIAAAA0vPorAAAAAXNSR0IArs4c6QAAAARnQU1BAACx \
                jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAEF9SURBVHja7Z0JPNXp/sd/RnfMbUySy/VPRtSg \
                pCjVmLQaWlU0lhaRakQlSbsaLdPepF1TKZU2U4iKKGWkJGVc17RIaaOS0l7o/L+cO0aH3+/8OJZz \
                js/39X71Msc5v/OM8zzf532e37Mw4/8QAAAqMiqx0GTZYdV+YxjVNkyz1nxoYdjNbbL3gfCjz57l \
                CEqegoaC/v70KdBnQZ8Iz8+OPmX6rOkTp88dlR+AKmHwJwCgIkPCrrebtILR78Gzp1HQNh46atz6 \
                oB1372Wiq5YS6LOgT4Q+F/p0+BqDfg/63OnTRxMAAK4AACuuqUXdtsZpDfVk1PR5fh81H2A3f926 \
                K+kXPhbno4eWKugToc+FPh36jPiOD6np06dPdYBqApoDAHAFAKq479Bxwa4mXW14fg1Vb2/uMXNu \
                THzM+7d56JilFvp06DOiT4o+L56fLNUBqgm4HwEAXAGATxgald3OcxWj04VXd6Khbz1i9KbgXY8e \
                ZaEzlgnok6LPiz41+ux4fcQ6Xag+UK1A0wAArgCAwC1N0G/PJW27aYy6IZ9eRNukl7f/ovMp53DT \
                QeZuSdCnRp8dfYK8dEHdkGoF1Q2qIWgmAMAVQOPFJeWd6erw5n1H8RxOGDpq3M6DIVjpINOrJOgT \
                pM+R5wAD1Q2qIVRP0FgAXAF/BdBIJygYz9/BtO/Lc3YCfSW9kn6hyh7o6dPbaVfOhoftD9q5efWq \
                xYsXzQXSjK3DD4ot/o9RbsXLEdv3pXrilFCAJgPgCgA0Lmyj7/GdoKDapo+Nw6bgXVUOJ5AikB94 \
                eXkMHzbI1KSTjs7XysrKighZCOYfysw//81z+oKB+3KqM2g4AK4AQGNhSNj11iNn8ZmgoKBt7OY1 \
                I/786cqzEy5fOrM+YAUpAvkBg5DR+EyJUVLlNcCgbkh1BrsvALgCAI2Cfvsul+6gwGPBvV7XfrPX \
                rK68wxI9Erh1nc2Q/qqqquhtZT8USgcYmrbkM8JENYfqDxoRgCsAIMdLHj6abztbunOz2F6huV4f \
                G4fg3w68fvVARBQunI92m+CqqamJPlauQrEpz/sRVH+oFlFdQoMCcAUA5FAUTNaf/OLb4XzWO4yZ \
                NDX+/GlBpfsO4WH7+1v3Q8cqz/cjvtIRW0OoFlFdgi4AuAIA8iUKV0tM1kUxpgPEdgMq35h5LfC/ \
                mZ1eeRrjgf1Bpiad0KXK+f2Iz1V4TV8wHUA1iuoVGheAKwAgD7imFpmsCmM6WvGZoLBy65anT29X \
                FoXwsP0GBgboSxtF8Jy+0NGK6hVOjgBwBQBkXxQuf+i49ACfTRS6WQ0LDj1Q5eEOF85HY0QB0xeq \
                3HqBahfVMTQ0AFcAQFZxSXnXccl+8adLN9cb6OB8PO54lds25+bewByFRjp94Qs1PidZUx3Dxo4A \
                rgCArI4oGC/aJ14UWrR1nOCZnJrItivw3Hkza3LfGyEH8VkTXqML+j2opmF0AcAVAJC9OQq8RhQ0 \
                9N28Zvx5/QqbKKRdOct/EwU1NTVTk06WlpY2Nja2CLmIYbYO5gPsSCj5jC5g7gKAKwAgS6seOq44 \
                Il4UWnZwnzMvJyeT9aih4nxHB1s+lqCiomJlZeXrOyMwcGtISMhvCDmKLUG7Bju5iT9rinRhxRGs \
                jABwBQBkZB+FgBPiJzO27OCxcHFu7g2OMwnT0xKUlJTEioKurq63t/fhw4djYqJPnz4dHR19/Pjx \
                SIQcxZ69IdZ8dKF9X6p72HcBwBUAkHa+DYwXu4+Cgrax16KfHz3K4j6/2MtrklhR0NH5euXKlfHx \
                8adOnQoLC6OvoUcQ8hg7du8ZPMqNFFPsvgtUA9EMAVwBAOnFMiRV7M6MTVubTl+2vMpNFCpSWHhX \
                S0uLWxSUlZX9/f3Pnz9PXz1DQ0PRocp3BO/ZM9jFU6wuUA3st+cSGiOAKwAgjQwJu97i+7FiRWH+ \
                mjVVni4tQkLCcbGDCsOGDUtOToYoNJ7YszfExtVDrC407zsKJ1ICuAIAUodt9D0t26libz3MW7W6 \
                sPCuWFEgFvnPFTufce/evWfPnoUoNKrYt28fn9EFqo1UJ9EwAVwBAGlhVGJha2c/McdMt+wwbeky \
                PiMKQoYMGcztCn369L548cLRo0fRfTbC0YXBY93FTHVUbUN1kmommieAKwDQ8LikvGvnu5lRN+Te \
                R8Fj4WKxcxQqIvb0B98ZPsnJyZjM2GjnLpSujFDj1AV1Q6qZ2NIRwBUAaPgVksbLDjM6XbhStpq+ \
                24xZYlc9iPDVV19xu0JAQMC5c+dq0M2Eh4dHRkYeL4tjx46FhYXVZycnlJvKZahP6RG+V0REaRlO \
                njzRIGWolZURfUY4i9mmSacL1U+sogRwBQAakh47E8VupTBiwuS79zKrJQpEkyZNuLdw3rlzZ1xc \
                HM9+JTQ0lPrC6OjomJgY6iCpUwwpi6NHj0ZFRdGD1F+Wd6J1FMIyxJQF9c30n1SAgwcPUhno3WNj \
                Y6kkwt2H6rQMpClUAPpTkCscPnz4wIH9wjKcPHmSyiCcKCor0rBl585uA0eI3XShb3AymiqAKwDQ \
                MNgcy/rSwp47U/cb5pSemVJdUSA+//xzrmMIFRV37dp16tQpPt+hqfOjzpj6x/37969atcrDw8PW \
                1ta6LH744YepU6f+8ssvZVs5xdTRkgqhAVD3TP3x3r17lyxZMmHChKFDh1IBBg4caG9v7+3tvWXz \
                Jnom9dYRERF1VAb6V7hR1a5duxcsWODs7GxjY1NeBl9fXyoDSQz9VcknZGXG6JpNmw3M+4tdFjE0 \
                KhsNFsAVAKhvnBIKWjnM4M7RnfvZnLtwpgaiUFuuIOwgyzq/MD+/+VZWVgYGBioqKgoKCuXjE6qq \
                qkZGRoMHD166dCn1o9Sb1m43SVejb+2nT5+mwvj4+PTp00dXV1dZWbni/4vwJIthw4YFBASQT5w4 \
                caLWyxAWFhYXF0e2NHnyZAuLnlpaWhX3xKQyqKurUxmcnJzIGGJjT0VFRcmKLixc8Yu2SS/uqqg9 \
                cjbmOQK4AgD1imtqkYHPBu6ZZXpd+0VER9ZMFGrFFYSiQB3kvn37qBsWu7MTdeEuLi70lZouW1vd \
                pLAMJAo7duygr+/kBNxlIGuhvpx0oRaVRSgKZ86cIRGxtLQkVeL+w5IxzJ07R3hfRlZ0wWfhkhaG \
                3cTOc8ThUgCuAED90WVjDPd8RpVvzH4N2fOxOL8BXYH6OaEo9O7dm+dJlfRV28bGhr5S11ZXTa5w \
                9uzZbdu2mZmZ8SwD9eXOzs6xsbG12FXHx8eTKJCI8CyDpqamp6cHKY5wXoX0uwIVcuKMuQraxtzz \
                HKneovECuAIA9cGQsOtNutpwr5BcsHbtuze5NRYFyV1BOEeBvqDzF4XycHBwoA4+PDxcwil+VAb6 \
                dn706FH+olCuLJ6engkJ5yTfPYLKQF1+cPAe/qJQrix+fvMTEhJkZZ7joUOHhoybxD3WRfXW5lgW \
                mjCAKwAgfpXjD3G5A0Izvtt+znRNuOmivaazAk2nrzedtq70X/qZHlkTTr+l59AzRdabjUos1Brh \
                zX1v2NHTq1pbKdTRuAL1cz/++CNT/aCueunSpaQLEnaT1NNTGWxsbGpQBlVV1S1btpw5c0bCr/XH \
                jh0jV+jVq1cNyqCj83VISEgt3pGph00XzG1GclfOVo4znS+8Qh4AcAUAqsAl5R31/aYBUSa+m9uM \
                nqMxaOI/zW1LlzvqdCndRqm5XmkmpX/pZ3qkfV/6LT2HnknPp1fRa+kK5A3t5u/k/urWc9APf16/ \
                IqEoSOgK1MfTr6ifEzs/gC0MDAxOnjwZGRkpyd0H6ukDAwP5HKtdZfTo0YN8RZLtH6gMJCsrV64o \
                n8tZ3Rg+fPjvv/8uQ5suBGzdJmZZhLqh0eL9bmnICQCuAEAFbKPvUWdvPGUN9f1MRysxW91VtZMS \
                vYpeS1cw8d/D6Pfgmm1u0ivuXIzkoiC5K5w/f37ChAmMBLF8+XLqaCXpt5KSkoYNG1rjApBkbN0a \
                ePr06RoXgDyDbKOnRY8al0FFReXAgf2kTTKkC37L16h8Y8a944JlSCoyA4ArACCgb05Do7JNl4e2 \
                dphRqgjchzXwga7AOZ9RQdt4c3CQJPMZa8sVwsPD4+LijI2NJXEF+kp94cIFSQb/o6Ki/v3vf0tS \
                BtKdixcv1rgM0dHRISEhFddn1iBmz54loTPV/zxHF68Z3IdLteg/zvFsPrIEgCuARg3lQbIEbbtp \
                3MMAtUlzvfFz/d6+eVgroiChK5w4ceLQoUMS9pEGBgYkHKQdNeux4uJit27dWuPBf2H07NkzMTGx \
                xrchqI9fsmQxI1nY2dkmJSXJ1mkR+/fv7+ng+r87ayziq+8dgL2fAVwBNFLGXSm2CErUd13I0xIU \
                tI1bGHZTb2+ubdKL/qWfxSw8Y5umMMQhJyeztkRBQlegPn7Lli0S9pEqKirUSQv3fq5RP31uxYoV \
                EpZB6CvHjh2r8U0QL6+pEpahT58+MucKFBt//VWv+/fcSyj77cOdCABXAI2PUYmFJksPlu67zPGN \
                qmUHA/P+gxwnuHvPn7dolf/mHRt279+899DOQ0fpX/qZHqHH6bf0nNJpYpxjueW7KZyKj65FUZDQ \
                FYT7DknYRzZt2vTw4cMnTpyoWV/1+++/L1u2TMIytGnThv4fJXEFDw8PCcvQq1dPWXQFitlLljdt \
                bcp9JwKbOQK4AmhcDI3KbjdpBetwgmob6vhHTvD2C9h2IOLkpav/efjo8fv37wVVBT1Ov6Xn0DPp \
                +fSqUmlgn/GgYvxdrax9qC1XoMd37Ngh4fi/hoaG8DTIGo8rrFy5UsJ+un379qdPn46IiKixK0yf \
                Pr1xjisIJy7YT5zCdRClapt2/nuwJgLAFUAj2h9J+4fpVa9xaNG2cz8b7/k/U8d/7dbt4uLiilrw \
                8uXL9PT0uLi44LKIioq6evXqq1evyp9Az6dX0Wt9/H6m61SdeTX0R7pPuZJ+QUpcgf4vwsLCVFVV \
                JekjO3bseObMmRrPFYiNLfUVKqckZfj+++/Pnz9f4zKcO3duxcrVErqCg4ODjLqCcMeFzta23Gsi \
                +odmIIEAuAKQf6wP/qE11LPK+w56Xft5+/0ccer0s8IXlccPMjMz161b5+Xl5eTk1LMshg8fPnny \
                5I0bN964cV3kyS9evKDr0NXomlV+RRs6atz5lHPS4ArUuSYkJHTv3l2SPtLJyVGSPjIiIiImJubr \
                r7+WpAze3t6SlOHEiROHQ49I6EyLFy8m5zgis7Fi/SbuJZQatlOxOxOAKwD5H1FQ7z+uynkJ9q5T \
                go9EPHv+vMobDdnZ2T4+Pt2riu+++27WrJkFBQWVX0VXo2vSlRmNKsYwrEeMTstIbnBXoEhMTPSZ \
                MaPGHaSCgsKGDesl2dtAeAtgzJgxkkyuFG6bKMnGkfR3GDx4UI3LoKmpGR4eXuMJnlISoyf7cN2J \
                UDc0WXsMmQTAFYA8z1HQGj6lcvpTb2/usywg43qWgCWKi4vnzZvXnTN27Qpiezld2dt/eZUn+9m6 \
                TGzwfRspqHujTk5XV7dmfWS3bt1IFCTcMzE2Nnbv3r013jty+PDh58+fl/Dkqvj4eEn2jhw/YQLZ \
                xhEZjz17Qzr0HcJ9ToTDmcfIJwCuAOQQp4QCbaeZlW89GJj3X78rpPDlKwF73MzK6i4uhgwZXFhY \
                yHaFZ8+f/7JzTxX3I5rrOXp6PXqU1bCuINze2M9vfg1mDFDvvnXrVsnPYhCuhqjZmRRkOSEhIXFx \
                cRKWQXg7hrSjBmUwMjI6Fhl58uRJWTk+iiMWrVrLvSbiG98tmOQI4ApADvdRMPDZUHkyYweLASHh \
                x4uKigScQf0Q2QB1Bqampt+VhZmZmUFZGBsb038KdeHixYscF6F32RUaRu9Yearj3JWrit4/blhX \
                EB6bZGdnV60FEcrKytOmTaP+tVbOeBSedWllZVXdkf/FixdJfnjVkQpnXVpY9KzuwVG//PLLuXPn \
                5EAUhH+H4eOncK0l1u9hE4EjKAFcAcgXPbYnVN5xmb7lH448UVJSIhAXS5YsIVHo0aMHuULnzp1J \
                CwwNDceOHevp6dmlS5eOHTsKdWHnzp3c16H3onesPLqg8o3Z8bgTDXvOJHUP0dHRUVFRtra2Kioq \
                PDvpH3/8kQyDXlUrhyvSRWJjYw8fPjxw4ECeNwJ0dXXnzp0THx8fHh5eK2Wgzj4uLm7fvn19+vTh \
                P6JAsnLmzBmSDPlwBYodu/dw787Uaswc19Qi5BYAVwByguPZ/C97OVaeo7Dj4BE+okAxdeqUgQMH \
                UFe0atWqNm3a6OjouLm5paen37p1a/2GDdRdCccVSCnEXorekd6X3l2kPOaD7SW5EyG5Kwi7auFe \
                RpMnT6b+j+N+BHXk5ubm8+bNo2/hJ06cqK1TmH8rC9IF6nRJxQwMDLgnM9K3/6VLl9airAjLINyf \
                KiQkxM7OjnsOh7q6uqWlZUBAAJWhtmRFesLXf2mVc3LLpwP33n0R6QXAFYA84JYm0J8VKDqa2rLD \
                8q1B7z98EPCLiRMnUCeSk5NTUFDQvW9/pS+0SRTOnj1LX0CfPX8+ePCgtm3bkitMnz6dz9Xofend \
                RXd4VG3z0y/rBDU9SqpWXKF8dOHkyZPU/zk5OZEQ6Oh8raqqqlQW9AP1ndRDu7i4BAUFUadei510 \
                RV2gotKV16xZM2zYMDMzMy0tLTIDYRnU1NTIIehLPwlNcPAeKgPJTa2XQbhFVUREBLnI4CFDTU06 \
                aWpqCsugrKwsLANZgq+v7/79+4UHYciZKFAcOnSo86AfOIYWVAdOdEl5hyQD4ApA9tc+RGZX3pzR \
                fsoc7smMIkFdwoMHDyZ5Lfw98dLKdb7WPfU+Fj3uazXSwmI4/dbf3586D3IFDw8Pnhekd6cyVB7q \
                +PN6asO6glAXqI8U9sE7duxYtMh/6tSpY8aMcXZ29vLyor5z167dkZHH6Gp110HSZSMjI6kM1G1v \
                27bNz8/P09ODyjB27Fhvb+9Vq1bt3bv3+PHjVIawsLC6KAO9r3D+BL3F4dAjWzZvmjt3Dn2+VIbx \
                48f7+PhQGUJCQkiqSK3K9UL+YsX6jVyTHNUNLX49hyQD4ApA5tH2XFV5mgLH8sgqg/qqmPj/2jl5 \
                Hvl1UE66xflw5Y+PJ4+y0TQ3H/Ig97XDRE8NDY1quYJwIWXliQuefgsb3BXKv9xTbx1TFvQVP7ws \
                hH0nPRIRUedfo4W9r9AYyiZSRFIBSGLKy1APX+WFZaB3pDKQFlBhhGWgn6kAVKo6MhXpCfoLDHJ1 \
                5xhaaPb9WOfkt8gzAK4AZBjb6Huigwot2m4I2iuoZvgvWj534caUlKGPkhlBVhk3mGu/MzHR5v+9 \
                sMrArIuW9jfkCl5eU6t1WSqJyKY3LQy73cxOb3BXqLySMKI0wiXZQUHCEHbSKEP9x5adOytPr/kb \
                Nf3uW+KQagBcAcgwrWcHiqS2zta2bDszcsSmTZvC93USvGAEdxlBZhk3GMEjRvCUeXbjX9OdVb5q \
                0dHU1LS6rkAlqbz9/sK1a6XNFRCNPMZ5z+E4C+3LviOx6zOAKwBZxTn5LWM6QGT+4J7fwgXVj4B1 \
                K0v+ZAS3yyzh+l9kMiXpjOAhs2uJ8mdNTdu1azdixIiPHz9W68pUHpEsrPet1ds3D+EKCOmJPXtD \
                tLv0ZR1aaNHWbP0JJBwAVwAySb99l0W6YQOLQVUeCiU2hv/gdnRTJ8E15sMF5n1qKR9SSn9+mcAI \
                7josnGvX5AstcgUzM7Pbt29Xb2ih8AWVSkRoziWdhisgpCqmzl3IcUjEP3vZY9YCgCsAmUTjx2Ui \
                Gc1/3dYaiEJubq5mq3YeXrOKHvk9if/X6wSGeHOWeZLYLevi5IInmZu3H2jRooWBgQHpwooVy6t7 \
                /aUbfhUpp/scP7gCQqpi//79eubWHEML322LR84BcAUgY4y7UswYfy+yp0LmzVs1cIXAwK3NmjXb \
                ELi7qKgoPXHJ46RBxIMkp/9e/u3yHznXsvLS/sjo0aPHv/71L3KFnj17XkpJqdb1b2TniOy1oN21 \
                X3W3fIYrIOo6pi9YxDG00Mza1fXyB2QeAFcAssSImAeiNyCsRvDcpfGTjvzG9YEDB7Rs2fLy5VID \
                yLh2/4+UUxlXzqZduZJ69RaRlpb25MmTmTNnUm9tZGREujB+woQ7d6pxJ4JKRWUT+ZaWffs/cAWE \
                LA0tqBta7ruMzAPgCkCW+HZTjEgu81m8urqiUFBQMGvWzLZt237/vaXwDMnnhS+SL/95KfUmWcLV \
                v+Lhw4dHjx7V1NTU1dU1MDDo0KGDn9/8Fy+qMTGCyiZS2t8ij9SuKxw+fCgpKSkagZAg5i9fzTG0 \
                oO40E4dPArgCkCW+9tkoksgiYuKrJQr0dT8gIKB79+4qKipLliwuf/DWrVsXL15MS0srd4XMzEx6 \
                cNCgQfRMEoU2bdqYmZkFBQXxfy8qm0hp569aXYuuoKCgsHXrVhKaPQiEBPHrr7+26PAd69CCTpeh \
                kdlIPgCuAGSGfzr4fJLFmuvde5hXLVc4dSq2Z8+e5AqampqXLl0qf/z169eXL1++cuVKRV3Iz89f \
                u3Zt06ZNv//++44dO7Zt27Z///78Jy5Q2UROrBg2YUotugKFhUVPKyurPgiEZNFCV59jG0ftaQFI \
                PgCuAGSnolh8cuaNgk6n4uLiaq19GF4WnTp1srOze/v2bcXf5uTkkD2kp6enlQW5QlZWFtlDx7Jw \
                cnIkVzA2Nv7R3V1450JsUNmohJ/MrrAcVruugEDUWjRtyaoL7fs6JRQg/wC4ApCRiqJvUTGFqXW3 \
                rNagwrJly3r37u3lNbVly5a/HTkqcm/izZs3ly9fvnjxonB0QRhPnjzx9/dXVFQcPXqUjY2Npqam \
                mZnZ/v37eb4jlfCTvfA69YIrIKQ0mnzJMbTQeV0U8g+AKwAZqSiaRhXzl8kg++qsfbhhYmIyadIk \
                Ozvbb7t3q7gn9Lt37woLC1+8eJGZmXny5Mn4+Pjz58+TN5ArZGdnkzoYGRnp6up6eHjo63/Tvn37 \
                4cOH379/n8+bUgk/GQj5pgtcASGtocAot2Ld8tnS2TW1CCkIwBWALFSUTxdM9nZ05e8KixcvNjc3 \
                9/Pza9my5cYN68uHE16/fp336NGDBw/y8vIePnx4+vTpyMhjsbGxZ86cSU5OTk9PL103MXs2pVJy \
                hREjRgiHFnhOcqQSfpJzNfThCgjpjc9VOBZPDvwtEykIwBWAPLvC/fv3u3fvPmHCBF9fX3V19Zyc \
                HHrw48ePhYWFDx4+vHf/PrlCbm7u06dPr127dvz4ceFastjYU6QL9PixyEgVFZUxY8bQy5s1a9ah \
                Qwd7+x/ev38PV0DI18iCIvOVDpsuaHmuRgoCcAUgz/cgDh48qKWltWzZMldX1wEDBggffPPmDVkC \
                QTbw8OFD+vfRo0f5+flJSUlRUVGxsbEnT54kXfjjjz/u3Lljamrao0cPuoKampqBgQH9561bt6Tt \
                HgSVzdSkU28EoqbRwqArxwzHUYmFyEIArgDkdm6jl5cX9aNBQUFjxoyeP38+PVJUVERmIBQFigcP \
                Hgh1oaCgIDs7myyhbFyhVBfOnDlDD86ZM8fNzS0gIEBZWZlcwcjI6Pjx49Izt1FXV9fFxWXjxo3h \
                4WHxCERNY8GaDRwzHHvgeAgAVwDyumby3bt3/fv3b9as2eHDh/39f9q2bRs9WFhYeO/evdy/4kFZ \
                CIcWnj59eunSJeGsBYqYmJjMzMyQkBBSjR07dpiZmeno6HzzzTc7xU1ZqLc1k5aWlsHBwaQ4AgRC \
                snj85EkLw25srtBizFxkIQBXAPK5F1Pe4yd6Bt2/bK75o+fshMSLaVcvl5SUCP2g3BUePnx4/68x \
                hvz8/Ds5OadOnTpx4kRcXNzvSRnbdh2wtbV1cHDw9fVduHChlZUV6cK2X39t8L2YKKgwCQkJIm70 \
                6tWr1whEjcLJ04d1aEG/B25DALgCkHZqtsfz4/ynLj+0muqhOsRKLyTsREnxe3KFO3fu5H4a5cMM \
                eXl5T58+/SM9PSoq8nhM8q3MuBle1v9U0dHT0+vevfvw4cOnz/Y3Nu91Jj6+Yfd4pjA16ZSYmEjv \
                dSklZf369Rs3bqR/58+fP2vWrNkIRI2i/2AbjtsQ3209g0QE4ApAqqnZ2VHvn/527TSTd5OJ/Y1Z \
                vaTnzkNH8/OfFhQUVHYF4ZQFiidPnuQ9ehQXnxxx/NzbR9ab5jCft7AgUTAy7qz0lcHCuXbz53x/ \
                48/khj07SkFBITw8TPhey1esUFVVVVNTo38VFRUVEAgJgmMPR9UfvJGIAFwBSDU1OZP6zXlBjqng \
                LiPIYwSPmWu/MyNHdZzitfTOndsvX7589OhRRVeoeFeCZOKPa88unVkjeMb8Gc5o6VkQBsa9e3Rv \
                fWqr8s1jGvcvOpW8zWvAM6lbtmxZ/nZz587Dij9E7e3h+BXHUVLY7xnAFYBUM+5KMWP8/SeZq2WH \
                zJu3WC3h2WbBPWvBTUZw/S+eM7G7GRVVfVc392vXrr1+/bpcDu7/tcuCMEgjsnMFz/50F9xmSm4x \
                6+dpWffr4Omsd3wDk3uSeRLL5J1iXt7ZybpNZHYOle2TA3i69it6/7gWXcHOzlb4Xh8/fhw+fDg6 \
                OET9bLTw7eZY5CIAVwBSjcaPy0Qyl/+6rVWLAllClsbflkD8yQjuMIInzCRHFeazlhMmTMjJyXn5 \
                8qXw1kP5UojyIFcQ3HMSZDKCHOb1f5jzwcqpe0sVISeKyQov5cGFgWyusHTDryLldJ/jVy1REOsK \
                /v7+wvd68eKFmpoaOjhEbUbT/2O9DTFqDhIRgCsAqabfvsuityEsBj0rfCHaVz8c84klVNSF58y1 \
                k4yOjqmyss6SJUvevn37+PFjVlfIsSl1BXrhA0aQymRH/M8ShGSf/NeHV1WMalB5qFSfZFjVNvHn \
                42rXFdauXfu/BRf376NrQ9TfbQjDni4p75CLAFwBSC/OyW8Z0wEi3fCe38JFu+s7FlW7wvWyoYXH \
                zErfrxmFdl27fXf33r2XL19WdoUHuXmlrkDXEbrCrVLPuBXBXDvyiS7kXXYuKXop8uZUHhGh0fvW \
                6vWrB3XkCjl376JrQ9T+bQg2V2iuN+DQf5CLAFwBSDWtZweKHphrbVvx3MjSyJ3C6gp/ls5zfJTM \
                jB3eYbTbgtTU1IKCgkdlx0eVu8LDhw8fPX31pOCl4IZG6fP/kowXvzMZoZ+4AvHy3sFPBhWeP6fy \
                iJRwIfXr1RSFaowr3LuHrg1RB7chWFdD6MzcikQE4ApAqrGNvsfo9xBZYrAhaO+nmyrMZnUF4hoj \
                uMvcuqRxLCou5nTq7dt3SBceloVwc4UXL148fCrIvhb+v0EFIVmlnnE7SnRo4UmaZ8V3ppJQeT7Z \
                7c6w283sdLgCQm5uQzSxsHdLQy4CcAUg3Wh7rhJJXnpd+2Vcz6pwD8KUyxX+ZEoXRzxj7l902hR4 \
                8FzCxcLCwpdlQZaQn5+fmZnpv2LPwW0DBA8ZwY0KL8xmXieXDi2U68K9s11fPggrf1sqA5VEpGye \
                fgtrIApwBYT03oZQN3SMz0ciAnAFINUMjcwWHVpo1tp+0oy/JzneZf6+d8DGXeZ9JjNnas/R42Yd \
                OnQwMTExISHh2LFjmzZtGus8Vv1rs9hflQXPP33JzVLunyzVhZxYgydpk17nRpUUvy+f0khlECmV \
                envzP6+nwhUQMhkcKyc3nUIiAnAFINW4pQn0ZwWKnLbAaOgv3rDt/YcP1H2+vtW1dA4jtyuUDS0s \
                mqKspGrWp0/vIUOGDBs2rE+fPl27dtXWadtSt+OT06WzIEVflc28v8rcv+T84t6Binsx0fvSu1MZ \
                ROZd/vTLOkFxPlwBIZPxhQbrOVKuPyERAbgCkHYcz+Z/2ctRNH8Zdttx8EhJSQl93Re8GCe4b116 \
                M+KW/if3ESq6wnMmcJXNYPspvr6+c+bMWbRokb+/v5+f3/QZc6Z4zXiZVJUrZDGCJzNFlkrSO9L7 \
                Vj6gr9sAu0ePsmomCnAFRMOHYlPW2xCmAzFlAcAVgAzQY3sCo9Ol8sSFw5EnSjd+LrlTuiPTiwjB \
                8/2Cpz8JHo8TncRArpBvnX7l3KWr/7l//35hYeHr169fvnyZl5d38+bNzMzMkgfjBDkioqBBoiAo \
                eS0iCvSOlacpqHxjdizmWI1FAa6AkPIpC07nsNkzgCsAqWfclWIDnw2Mmr5IFutgMSAk/HhRUVGF \
                Dv1jqTqQNzyaLrjvUDrecN/6Y97kUpngCHoJPZn84EaZJdyzLt00+lNRoHfZFRpG7yiaSTX0565c \
                Vd1NneEKCKkL5VZsutBzRyKyEIArABnAKaFA22mm6MSFZq0NzPuv3xVS+PKVaPdf/FzwNrNUEd6c \
                /1j0WOwZlaVPJj946l/6b6lYfBTZn5HepfKIApXH0dNLkrsPcAWEtISSGpsraE3fgBQE4ApARtZE \
                RGVrDZ9SOZGptzf3WRbwyULKWg26srf/SnqXym9t6zLxz+tXJBQFuAJCyqcsNOnvivwD4ApAZhgS \
                dl29/7gq0lnLDvauU4KPRIju6ihZ0NXomnRl0VUPZViPGJ2WkSy5KMAVENI+ZUGni3PyW+QfAFcA \
                MoP1wT+0hnpWvhkhnO3o7ffzydNJVdySqGbQFeg6dLUq7juUrZAcOmrc+ZRztSIKcAWEtAT7LgtD \
                wm8i+QC4ApCx0QXtH6ZXnuoo3AT6WysHnwXLD0ScvHbrdnFxcbUUgZ5Pr6LX0hXoOiJbOJdPZhzp \
                PuVK+oXaEgW4AkJagv186s5rIpB5AFwByN7cBYMff668kLL8e7+Bef+RE7z9ArZRx3/p6n8ePnos \
                3LupctDj9Ft6Dj2Tnk+voteKnB5ZcXmk1wL/6zfTalEU4AoIaYl/qLLuyOS+DGkHwBWATK6MMFm4 \
                +0sL+yrvR5TPY6COf5DjBHfv+fMWrfbfvGPD7v07Dx0VQj/TI/Q4/ZaeU6oILTuwXkq1TTerYau3 \
                bX369HbtigJcASH90xuZfmOQcwBcAcjqvgsWQYn6rgsrnxlRJQraxi0Mu2mb9BJCP9MjfF6o3t7c \
                Y+bc43HHJdxHAa6AkNXpjbpd3a6WIOcAuAKQVRzP5psuD9W2m8bTGKoF+YSj26TNwbsk30QBroCQ \
                4emNzfUczz5FtgFwBSDDuKWVzmAgY2jtMKN2jEG1jV7XfmN+nLxh187SHRRqeigUXAEhY/GlFluj \
                sNybglQD4ApAHrCNvtdizNyaK4KGPinCQAfn2YuWBP928GZ2ep0qAlwBIXXBvntjx2WHkWEAXAHI \
                CRqTV3NMdfx7VyUNfQVt46atTbVNenXuZ0N+4DbZe8Hq1aQIyamJb988rB9LgCsgpCuaNGNrPtSy \
                kF4AXAHICU1sJrEluxGe3v5r1/r/vKwU+mHTxpWBW3ceDImIiSI/uHsvs+TDk/pUBLgCQoaWQlDL \
                QnoBcAUgL5Wsc3+2ZBd95kSDqABcASEPSyE690d6AXAFIB+THD8yrTqyJbus+pp/AFdAyHCwuUKr \
                jtS+kGQAXAHIPGOSXrFuzaShX8+zEOAKCJkM9mWT1L6QZABcAcg8QyNvsX0rUjH+TjpFAa6AkK5g \
                XzZJ7QtJBsAVgMzTZ9cFtjRnPMAOroBAiI8v/s3WiKh9IckAuAKQebr8EsWW5ga6uMMVEAjxwX6C \
                FLUvJBkAVwAyj6H/XrY05zZjNlwBgRAf7FssUPtCkgFwBSDzaPtsZEtzs5b+DFdAIMQH+xYL1L6Q \
                ZABcAcg8KhMWs6W5lZs3wRUQCPHx2eesE4QnLEaSAXAFIPubNjr4sKW5oIN74QoIhPhQaMK6daOD \
                D5IMgCsA2a9h1q5saS4qNhKugEDwcIXPWLdjsnZFkgFwBSD7Naz7MLY0l3TpHFwBgeAjC6yu0H0Y \
                kgyAKwDZr2GmrIdB/PfPy3AFBIJXsLmCUW8kGQBXALJfw4x6s6W52zkZcAUEQiJX0P8WSQbAFYDs \
                1zD9b9nS3OPHWXAFBEIiV9A1Q5IBcAUg+zVM14wtzRU+y4ErIBASuUIrUyQZAFcAsl/DWpmypbk3 \
                Lx/AFRAIiVxB3RBJBsAVgOzXME0jtjRX8uEJXAGBkMgVmrVGkgFwBSD7NUy1DVuOk1pRgCsg4AoA \
                wBUAXAGugIArAABXALgHAVdAwBUAgCsAzG2EKyAwtxEAuALAmkm4AgKugDWTAK4AsBcTXAGBqIEr \
                YC8mAFcA8lDDsMczAlF3roA9ngFcAchDDcPZUQhE3bkCzo4CcAUgDzUMZ1IjEJIGzqQGcAUg3zXM \
                2pUtzUXFRsIVEAgeqvAZqytYuyLJALgCkHmaOPiwpbmgg3vhCggED1dowtaIqH0hyQC4ApB5VCYs \
                ZktzKzdvgisgEOLjs8/ZGhG1LyQZAFcAMo+2z0a2NDdr6c9wBQRCfCg2ZWtE1L6QZABcAcg8hv57 \
                2dKc24zZcAUEQnw0acbWiKh9IckAuAKQebr8EsWW5ga6uMMVEAjx8Q9VtkZE7QtJBsAVgMzTZ9cF \
                tjRnPMAOroBAiI8v/s3WiKh9IckAuAKQeYZG3mKdlmX8HVwBgRAfX2qxNSJqX0gyAK4AZJ4xSa+Y \
                5npVZzoN/bdvHsIV6jOMjIzc3Nz8K0Tv3r1rdikPDw96uY2NDbryOo+vdKpuQc31qH0hyQC4ApB5 \
                3NI+Mq06sn0ryspOhyvUW+jq6oaEhOTk5AgqxE8//VQz58jLy6OXx8XFoSuv82A9ZLIjtS8kGQBX \
                AHJRyTqzHgkRfeYEXKHeYtWqVe/fv6c+Pjg4WMJxBbhC/YWCIqsrdO6P9ALgCkBetm60mcSW7DYG \
                bYcr1FtQaanMO3fu1NXVlfxquAdRT8G+uQK1LKQXAFcAcoLG5NVsyW6K309whfoJNTW19+/fU5kH \
                DBiA/leWgn1zBWpZSC8ArgDkhI7LDrMlux4/jIEr1E8YGBgIy0w/VGkS/v7+vr6+9LONjc28efOE \
                dyhGjx4t8kwvL6+KUyPd3NwqX83e3p5+ZW1tbWRkJBx+oKAXVr7foaurS2/hX1XUeNKlvIWSGlvz \
                oZaF9ALgCkBOsNybwrpssv23JR+ewBXqLspXPWzcuFFYZvqhvD8mJ6hoEgUFBdS1p6amCkcgKG7e \
                vEmPVLzgrVu3Kk6NTExMrPymhw8fpl8dP348NDRUOK1BePGYmJiKtz/o5+3bt9NbCKqKmk26bFQL \
                JqllIb0AuAKQExzPPmVU21Sd71q0zc29AVeou6C+XMAer169qugKwpmP5ZMfk5KS6EH6z4pf8cvH \
                FUgpuF2B5IAuSBehJ9MF6b3oP6dNm1b+tAULFojMtczIyBC+EOMKfBZMUstCegFwBSAvyyavljB6 \
                3di+G506FwNXkJJxBQrqrT08PITf/q2trYULLDdt2lT5ytu3b+d2BfIAeg5dRDiEkJCQQA+GhYWV \
                P+3SpUv0yMGDB8sHG+zt7elV5ApGRkaQBDGLIHS7UstCegFwBSBH9azfGLaUt2rrZrhCg89XKP/t \
                pEmTKj5OXTs9ePLkyRq4wtWrVyvecaj8/LS0tCpdgQKuIHYRBLUpJBYAVwByRQv3ZWwpb/Q0X7iC \
                9LiCyG85hECsK9C/3M9fsmRJlfcgLly4AEn4X7CfGkVtCokFwBWAXNF5TQRbytPrO1RQnA9XkGZX \
                OH36dF24wrRp08gVKu4jSd4QHx+PPRv+jqb/x9ZwqE0hsQC4ApArhoTfZB1KbdnhaX42XEE6XSEu \
                Lo4ePHToUF24woULF+iRmTNnls+f8PDwwJRGXhMbm7WmNoXEAuAKQK5wTn7L6HRhy3qxZ2PgClLi \
                CiNGjChf0Eg9d0FBwatXr8aNG1frrlC+N1SVF0eImdio04XaFBILgCsAeaNJf1e2xDd3+Qq4gpS4 \
                Qnx8vPArfnBwcF5eHnXnu3fvpn5d+DQjI6PyMQDhmsmcnJzyR8qfxtMVhFsv0HVEdmGyt7eHJ3BP \
                bKTWhJQC4ApADtGavoEt8XUbNhKuICWuUDEyMjKog6+4JMHR0ZFjt4byK/O8B3Hw4MHyTZ9E3ldk \
                A6hGGuw7NlJrQkoBcAUgh/TckciW+Jq2Nn396gFcoU5DuItzxW//VbpCxd0X6Pu9yClTFccVKkf5 \
                lYV7PIsMD9jY2FTcE5quHBMTU1BQUPHQS4r4+HjhJMdaOeBKtkO5FVuTodaElALgCkAOcTpXwKgb \
                suW+lKuJcAWpHXWoixAugkhLSxNxgt69ewsHGywtLTFZoWrUDak1IaUAuAKQQ9zSBIzpQLb0t3zT \
                RrhCo3IF4S0JcgXhxo7l4xYeHh7kCq9evWrs4wocuzCZDqTWhJQC4ApATndkcv2JLf11sR0FV2hU \
                rjBu3LhXZSE8MEIYwrOmhBMqG/sNiC80WHdhcv0JyQTAFYDc8u2mU2zpT0Hb+NGjLLhC43EFNTW1 \
                FStWZGRkkC6Uz2okS6BH6M+LPZ45dlboviEayQTAFYDc4hifzzFlITTyKFxBOmc+1t2b2tvb+/r6 \
                VjzLih6pzzLI4mQFh9OPkUwAXAHI85SFJhb2bEnQxWcWXAGBKI0mX7HurGBhj8kKAK4A5BydmVvZ \
                kqB2l77v3uTCFRAIpmlLtmZCLQhpBMAVgJwz4NB/mOZ6VedB1TbJqb/DFRC4AcF6A6K5HrUgpBEA \
                VwByjkvKO8awJ1sqnLH0Z7gCAjcgWF3BsCe1IKQRAFcA8o/qqDms51ObW0vJbQi4AqLhbkCwnkNN \
                bQcJBMAVQONYObk5lvVrU4u2F1LOwRUQjfoGBPtqSWo7SCAArgAaBU4JBRznU09Z4A9XQOAGRJXn \
                UFPbQQIBcAXQWGg2fDLHaghpOEcKroCQthsQ1GqQOgBcATQizNZFsX55Um0Tfz4OroDADQgRqNUg \
                dQC4AmhEOJ7N57gNMcbbF66AwA0IkRsQ1GqQOgBcATQuWthPZz0ax7Bbg58NAVdANMQNCNYtmKi9 \
                IGkAuAJodPTYFs/6FapZ612HQuAKiMYVnylxtAhqL0gaAK4AGh2jEguZ9n3ZMmM3G/ui94/hCohG \
                FOyHUFNLofaCpAHgCqAxouW5mjU5auhfupIIV5AwlJSU0AXLwaxGailIFwCuABopg3/7k+OI6nG+ \
                s+EKkoSpSSd/f39HR0cFBQX0xdIen6twHEI98LdMpAsAVwCNlHFXir+0dOaY4Zh9JwOuUJPvqAoK \
                dnZ24eFh7969y8zM9Pb21tH5Gt2xNI8qMMqt2BrCP/uMck0tQroAcAXQeOnMsdFCs9aL1q2DK1Q3 \
                dHV1p/v4pKenC/6KgoKCoKAgS0tL9MlSGk2+5GgFJmvCkSgAXAE0akr3e2af4aj3rdXTp7fhCvzD \
                ysoqODj42fPngkqRkJAwfvx4VVVVdM1SF+xLJal1YF9nAFcAQKA9LYBjD8fdh/bDFXgOJ0ycODEx \
                MVHAHnfv3qWSm5mZoXeWlaWS1DqQIgBcAQDB0Mhsjj0cO1vbvnxxD64gdoLCqlWr7t+/LxAXRUVF \
                UVFR9vb2ioqK6KalfamkThdqHUgRAK4AgMAtTaDuNJPjlOojx8PgCmJdwdvbO+XyFQG/yMjImDVr \
                loGBAXrqhh9UYF8qSe2CWgdSBIArAFCK5b7LHIsnzYePrP+TJ2XuHoSSktLgIUNDQ0Pfvn3LRxde \
                vnx54MABa2tr9NdSOqigbkjtAskBwBUA+B+ulz80s3bl2Jcp7GQEXIFPGBkZLVy48MaN6zwHGJKS \
                ktzd3TU1NdFrS9ugArUIahdIDgCuAMDffLctnmnRlnVowWZkPc9akN01k0pKSqNGjYqJiS4pKeGj \
                C7m5uYGBgebm5ui7pWhQoUXb73AABIArACCCc/Lbf/ayZ02davqHj/0GV+Af1Pdv3LiRz2xHYZBb \
                kGEoKyujB5eGQQVqC9QikBYAXAEAUczWn+AYWug2cMSzZzlwBf6hrq4+ceLEpKQknrpw48b1JUuW \
                GBkZoR9v8EEFagtICACuAEBVQwsXXn3ZdyRHAt2xfy9cobphbW0dHBxcWFjIRxfevn0bGhpqY2OD \
                IyQacFCBWgG1BSQEAFcAoGq6b4lj1PTZcmgHiwH3H1yDK1Q3dHV1fX19MzIyeA4wpKamenlNwxES \
                dRYKzD//zXG7jVoBUgGAKwDANWuh2fdjObaxm7dqNVyhBqGoqGhvbx8eHvb+wwc+upCf/zQoKKh3 \
                797o2Gs//vEVRw2n+o+ZCgCuAIAYLH49x7HXgnp784xrl+EKNQtTk06r16y5c+c2zwGG+Ph4V1dX \
                FRUV9O+1N6agyHGkJNV8qv9IAgCuAIAYXFLeqQ6cyPHFy2HajPdv8+AKNQtVVVXq/s+ePctTF0gs \
                Vq9eTZKBXr6WlrS24KjbVPOp/iMJALgCAOLpG5zMtOzAlk8VtI0jT0XBFSSJPn36BAUF5ec/5aML \
                RUVF4eFhOEKirqc0Up3vvfsimj+AKwDAi3FXiluNmcPx9ct8sP2jR1lwBUlCR+frKVOnpqam8j9C \
                wtfXV1dXFz1+nayTbNaa6rxrahGaP4ArAMAXm4gsRr8Hx1nVP/2y7mNxPlxBwrCxseF/hERhYWFw \
                cLCVlRU6/RrNL/2Sa1BBvwfVeTR8AFcAoBq4pQn0ZwVyfAlTb29+/tJZuILkYWRktGTJkhs3bvAc \
                YEhMTHR3d1dXV0fvX70pjU1bctTnb3y34EhJAFcAoNo4ns1v0tWGI71ajx5Xdzs5Nh5XoFBWVh49 \
                enRMTDRPXcjNzd28eTOOkKitKY1Uzx3OPEaTB3AFAGqCydpjHOsnGQ39tb9ugyvUVlDfHxgYSB7A \
                /wiJkSNHKikpwQTE3X1oynX3Qd2Q6jkaO4ArAFDTrZkuvNKwncrxhUzbpNeV9AtwhdoKTU1Nd3d3 \
                /kdIXL9+3c/PD0dISHL3gWo4dnQGcAUAJKJ/aAbTvi9Hqh3q5v706W24Qi2GtbX1gQMHXr58yUcX \
                Xr9+HRoaOnjwYFhBDe4+UN2mGo5mDuAKAEg6ybGd/x5GtQ3HnYglGzaUfHgCV6jFMDAwmDdv3n// \
                +1+eAwyXUlImT56spaUFN6jG3QfVNlS3MaURwBUAqAVGJRa26D+Oe03EqfhouEItfx9WUnJwcIiK \
                iiopKeGjC4+fPNm+fTuOkPg7PlPivvtAtZrqNho4gCsAUDv025fK6HThSLs9hzjk5GTCFWo9zMzM \
                1q1bd/fuXf5HSLi4uOAICTGHSRI6XahWo2kDuAIAtXgn4qO+dwDXnYjmeuPn+r198xCuUOuhqqo6 \
                fvx4/kdIZGdnr1y5srEfIcF5mCTVZKrPVKvRtAFcAYBa3m5B1cqFI/8qaBtvDg6qrc0c4QoiITxC \
                oqCggI8uvH//Pjw8zM7OTkFBoZFOU+A4TLLs7gPVZzRqAFcAoPbpuzeFa+PnsiWUcedi4Ap1FDo6 \
                X3t7e1+9epXnAEN6evp0H59Gd4SEuGkKTPu+liG4+wDgCgDU2Z2IdvN3Mmr6XBMXBv3w5/UrcIW6 \
                ugmvoDBs2LDQ0NB3797x0YVnz583siMkxE1TUDc0Wrwfax8AXAGAul0ToTXCmysXN2vt6Okl+Y4L \
                cAWOMDIyWrp0aVZWFv8jJCZOnKimptYIdlNozl05WznOxM5LAK4AQJ0zJOw69zkRjIb+grVr373J \
                hSvUXSgrKzs7O8fFxfHUhfv37wcEBJiZmcn1fEZlrt0Uys59sDmGwyQBXAGAeqHLxhjuJZQq35j9 \
                GrJHknmOcAU+YWHRMzAw8ObNm3z2YCguLo6Kiho5cqSmpmYjnM9INZbqLRovgCsAUE+4phYZ+Gzg \
                nrig17VfRHQkXKGugzr+2bNnv//wgf8REu7u7o1uPqO6YTvfzVRv0XgBXAGA+sMpoaCVwwzue8Od \
                +9mcu3AGrlCnYW5uvnHjxqKiIv6nUw4dOlS+pjMqipnP2Ky19sjZ2KIRwBUAaABsjmV9aWHPnaP7 \
                DXPKuHYZrlAn0/iUlEaNGkV9/9u3b/lYQm5ubmBgILmFvInCF2rclbB531FDo7LRYAFcAYCGocfO \
                RO5TKAn7H6fcvZcJV6j1pRALFy68ceM6z+GEpKQkd3d3uZupoCDmGMmy3RT6BiejqQK4AgANueOC \
                8bLD3PMcGTV9txmzHj3KgivU1hYLNjY2oaGhPIcTXrx4ceDAAWtra/lcIcm58IFqJtVP7OUM4AoA \
                NDAuKe/a+W5m1A25V1F6LFxcrU0X4ApVho7O11OmTk1NTeU5nJCRkTFz5kwDAwM5/Ft8riJGFNQN \
                DXw2UP1EIwVwBQAanlGJha2d/bhOliJadpi2dNmzZzlwhRpH7969g4KCHj95wscSioqKoqKi7O3t \
                FRUVG+FWClQbqU46JRSgeQK4AgDSgm30PS3bqdx3jhW0jeetWl1YeBeuUN1QUVFxdXWNj4/nOZyQ \
                k5NDfyK53XmJRIF7K4Vmrak2Up1EwwRwBQCkiyFh11t8P5Y7gzdtbTp/zRo+owtwhfIwNem0evXq \
                O3du8xSFs2fPurm5qaqqNlpRaNbbiWojmiSAKwAgjViGpH7x7XCxujB92XKxcxfgChSKior29vbh \
                4WE8t08oKCgICgrq06eP3P5FeIgC1cA+uy+gMQK4AgDSy7eB8YzpALE3I6YtXca9MgKuoKur6+vr \
                m5GRwXM44erVq97e3jo6X8utKHyuIlYUqO5RDUQzBHAFAKR9FaVJwAmxmy6QLngsXJybewOuUGVY \
                WVkFBwcXFhbysYR3796FhoYOGzZMQUFBnkWBezJj2VYKVPewQhLAFQCQBV24WtJxxRFGv4eYzN6y \
                g/uceWzbNDVaV1BXV584cWJiYiLP4YSsrKylS5caGRnJ8Y4SvERBvwfVOqp7aIAArgCAbOCaWtRx \
                yX7xuqCh7+bt++f1K3AFYZibm2/evPn+/fs8RSEuLs7Z2VlZWVmeRUHshktCUViyH0dDAbgCALKm \
                C5c/GC/aJ14XWrR1nOCZnJrYyF1BSUlp5MiRMTHRPC0hLy8vMDDQwqKnPK8AUVBklFT5iALVNKpv \
                aHQArgCA7OGS8o7X6EJzvYEOzsfjjn8szm+crmBgYODn53f9Ot/DHZKTkz08POTucIdP4zMlsYdC \
                lY8oYHNGAFcAQLZHFzouPSB2qiPRzWpYcOiB92/zGpsrDB48+MCBA69fv+ZjCfQ0evLAgQPlfE8J \
                xaZij5kWTmak2oURBQBXAEAe5i6YrApjOlqJTf16Xfut3LpFuPVCY3AFLS2tyZMnX0pJ4TmckJmZ \
                6efnJ5+HO4hsotC0pXhR6GhlsvIo5igAuAIA8rMywmRdlNh9FwiVb8y8FvjfzE6Xe1ewsOi5fft2 \
                noc7lJSUREVFOTo6KikpybUmKPDaRKFsHwWTXyLHXSlG4wJwBQDka9+F9SfF7uooXBwxZtJUxc+/ \
                kldXUFFRcXFxiYuL4zmccPfu3fXr18vt4Q7VnclYtjMj1SUsjwRwBQDkUxfMt51V7TdGvC401ysd \
                hVZsKn+uYGrSacWKFdnZ2TxFISEhYfz48WpqavI/QYHPTMZmrZv3HUW1CBsuAbgCAPJMv32XNQZN \
                FHOAtRDShX8ol45Ly4UrKCgo2NnZhYeHvXv3jufhDsHBwZaWloy8jyfwnaCg2oZqTr89l9CIAFwB \
                APlnQGhG65GzGHVD8d2DcqvScenPlGTdFXR1daf7+KSnp/McTqBnTp8+nV4l555Anyx9vnwmKKgb \
                Up2hmoPmA+AKADQWbKPvGbgvZ3S68Bl2Ll0+9+n9CNlyBeHhDs+eP+d5uEN4eJidnZ2ioiIWRv4P \
                nS5UW6jOoOEAuAIAjQunhALj+Tv4bL3wv/sRn6uUTn+TKVdQU1MbP348/8Mdbt26tWLFClOTTvI/ \
                jZE+TT73Hco2UegwdzvVFjQZAFcAoDHikvLOdHV4s95OvPqMr3RKp7+VDTDIhCuYmZkFBATcvXuX \
                /+EOY8eOVVFRaRTTGHmsdyCoblANcU5+i8YC4Ar4K4DGvDhC0Gf3BW27abymL/w1wDDJd05JSYnU \
                uoKSkpKjo2NUVFRxcTEfS3j85Mn27dvl/HCH6g4nqBtSraC6QTUEzQQAuAIAgqFR2e08V/GdvvCV \
                jl7XfhuDD1AXK4WuIDzcITMzk+dwwqWUlMmTJ2tpaWE4oeIEBaoPVCvQNACAKwDwN6MSCzv6BTXp \
                asOrL2nWWr29+eSZCw+EhUtVhzhw4MDqHu4wePBg+V/swH84oVlrqgNUE6g+oFEAAFcAQBTXyx+6 \
                bY3TGurJqOnz6ldU23SzGlZxzmPDDid4eHgkJyfzHE64du1aPRzuYG9v7+7uPr4hws3NzbxvP0at \
                VeliB57DCWr69OlTHcBxUADAFQDgYkjY9XaTVog/ybqKOY8KDbjP0rp16/Ly8vgf7uDk5FQPhzuk \
                pqbm5uberfdISk6Z/fNq8wF2TMsOfD9H/R70udOnjyYAQGX+HxRcVMs0ZpdiAAAAAElFTkSuQmCC"

        return png_output

if __name__ == "__main__":
    print("RRD HELPER")
    # rrd_fping("CAFE", "172.31.3.1", [25.6, 49.7, None, 36.6, 36.5, 34.5, 35.8, 29.5, 26.5, 41.6, 117.0, 30.1, 45.4, 34.4, 56.8, 37.8, 24.4, 35.6, 25.9, 32.2, None])
    # print(rrd_graph("CAFE", "172.31.3.1"))
