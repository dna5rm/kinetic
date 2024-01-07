from django.shortcuts import render
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.utils.timezone import now
from .models import agent, host, stat
#from .forms import ...
from .rrd_helper import rrd_fping, rrd_graph
from re import sub
from statistics import median, stdev
from datetime import datetime, timedelta
import json
import timeago

# Create your views here.
#@login_required
def main(request):

    if 'query' in request.GET:
        host_query = request.GET['query']
        stat_temp = []
        stat_output = []

        for host_row in host.objects.values('address','hostname','agent').filter(hostname__contains=request.GET['query'],enabled=True).order_by('agent'):
            if agent.objects.values('active').get(agent=host_row['agent']):

                # Fetch stats for host.
                for stat_row in stat.objects.filter(address=host_row['address'],agent=host_row['agent']):

                    if stat_row.loss != stat_row.pings:
                        state = ( True, sub(' ago$', '', timeago.format(stat_row.last_change, stat_row.last_updated)) )
                    else:
                        state = ( False, sub(' ago$', '', timeago.format(stat_row.last_change, stat_row.last_updated)) )
                    
                    stat_temp.append([
                        host_row['hostname'],
                        stat_row.address_id,
                        state[0], state[1],
                        round(stat_row.median, 2),
                        round((stat_row.loss / stat_row.pings) * 100),
                        round(stat_row.avg_median, 2),
                        round(stat_row.avg_min, 2),
                        round(stat_row.avg_max, 2),
                        round(stat_row.avg_stdev, 2),
                        round((stat_row.avg_loss / stat_row.pings) * 100),
                        timeago.format(stat_row.last_updated, now()),
                        stat_row.agent_id
                    ])

        # Append number of host matches.
        for host_match in stat_temp:
            match_row = [len([row for row in stat_temp if host_match[0] in row]),[row for row in stat_temp if host_match[0] in row]]
            if match_row not in stat_output:
                stat_output.append(match_row)

    else:
        host_query = ""
        stat_output = []

    return render(request, 'fping/index.html', {
        'agents': agent.objects.filter(active=True).order_by('agent'),
        'query': host_query,
        'stats': stat_output,
        'count': len(stat_output)
    })

#@login_required
def report_agent(request, agent_id):
    stat_output = []
    stat_rows = stat.objects.filter(agent=agent_id).order_by('address')

    for stat_row in stat_rows:
        if host.objects.filter(agent=agent_id,address=stat_row.address_id,enabled=True):

            # Calculate last time the state changed
            if stat_row.loss != stat_row.pings:
                state = ( True, sub(' ago$', '', timeago.format(stat_row.last_change, stat_row.last_updated)) )
            else:
                state = ( False, sub(' ago$', '', timeago.format(stat_row.last_change, stat_row.last_updated)) )
            
            stat_output.append([
                host.objects.values_list('hostname').get(address=stat_row.address_id)[0],
                stat_row.address_id,
                state[0], state[1],
                round(stat_row.median, 2),
                round((stat_row.loss / stat_row.pings) * 100),
                round(stat_row.avg_median, 2),
                round(stat_row.avg_min, 2),
                round(stat_row.avg_max, 2),
                round(stat_row.avg_stdev, 2),
                round((stat_row.avg_loss / stat_row.pings) * 100),
                timeago.format(stat_row.last_updated, now()),
                int(host.objects.values_list('agent').filter(address=stat_row.address_id).count())
            ])

            stat_output.sort(key=lambda i: str(i[0]), reverse=False)

    return render(request, 'fping/agent.html', {
        'agent': agent_id,
        'agents': agent.objects.filter(active=True).order_by('agent'),
        'stats': stat_output,
        'count': len(stat_output)
    })

#@login_required
def report_down(request):

    stat_output = []
    stat_rows = stat.objects.order_by('-last_change')

    for stat_row in stat_rows:

        if stat_row.loss == stat_row.pings:

            agent_row = agent.objects.values_list('active').filter(agent=stat_row.agent_id)[0][0]
            host_row = host.objects.values_list('enabled','hostname').filter(address=stat_row.address_id)[0]

            if agent_row and host_row[0]:

                stat_output.append([
                    stat_row.agent_id,
                    host_row[1],
                    stat_row.address_id,
                    timeago.format(stat_row.last_change, now())
                ])

    return render(request, 'fping/down.html', {
        'stats': stat_output,
        'count': len(stat_output)
    })

#@login_required
def report_loss(request):
    
    stat_output = []
    stat_rows = stat.objects.filter(loss__gte=1)

    for stat_row in stat_rows:

        agent_row = agent.objects.values_list('active').filter(agent=stat_row.agent_id)[0][0]
        host_row = host.objects.values_list('enabled','hostname').filter(address=stat_row.address_id)[0]

        if (agent_row and host_row[0]) and (stat_row.loss != stat_row.pings):

            stat_output.append([
                stat_row.agent_id,
                host_row[1],
                stat_row.address_id,
                round((stat_row.loss / stat_row.pings) * 100),
                stat_row.median,
                timeago.format(stat_row.last_updated, now())
            ])

    return render(request, 'fping/loss.html', {
        'stats': stat_output,
        'count': len(stat_output)
    })

@csrf_exempt # having issues with CSRF token under apache, disabling.
def fping_agent(request, agent_id):
    if request.method == "GET":
        send_string = {}

        target_hosts = host.objects.filter(agent=agent_id,enabled=True)
        send_string['probe'] = 'fping'
        send_string['opts'] = [ '-C 20', '-q', '-B1', '-r1', '-i10' ]
        send_string['targets'] = []

        for target in target_hosts:
            send_string['targets'].append(str(target))
        
        csrf_token = get_token(request)
        return HttpResponse(json.dumps(send_string))
    
    elif request.method == "POST":
        post_data = json.loads(request.POST['data'])
        fping_data = post_data['data'][0]['target']

        for fping_row in fping_data:

            # Locate the row to update
            stat_id = stat.objects.get_or_create(agent_id=agent_id,address_id=fping_row['host'])

            # Process general sample information
            stat_sample = stat_id[0].sample + 1
            stat_pings = len(fping_row['result'])
            stat_loss = len([i for i in fping_row['result'] if i is None])
            
            # Stat: Median
            if stat_loss != stat_pings:
                stat_median = median([i for i in fping_row['result'] if i is not None])
            else:
                stat_median = 0

            # Stat: Min
            if stat_loss != stat_pings:
                stat_min = min([i for i in fping_row['result'] if i is not None])
            else:
                stat_min = 0

            # Stat: Max
            if stat_loss != stat_pings:
                stat_max = max([i for i in fping_row['result'] if i is not None])
            else:
                stat_max = 0

            # Stat: Std. Deviation
            if stat_loss != stat_pings:
                stat_stdev = stdev([i for i in fping_row['result'] if i is not None])
            else:
                stat_stdev = 0
            
            stat.objects.filter(id=stat_id[0].id).update(
                pings=stat_pings,
                loss=stat_loss,
                median=stat_median,
                min=stat_min,
                max=stat_max,
                stdev=stat_stdev,
                prev_loss=stat_id[0].loss,
                last_updated=now()
            )

            # Update stats with average values
            if stat_loss < stat_pings:
                if stat_id[0].sample < 0:
                    stat.objects.filter(id=stat_id[0].id).update(
                        sample = stat_sample,
                        avg_loss = stat_loss,
                        avg_median = stat_median,
                        avg_min = stat_min,
                        avg_max = stat_max,
                        avg_stdev = stat_stdev
                    )
                else:
                    stat.objects.filter(id=stat_id[0].id).update(
                        sample = stat_sample,
                        avg_loss = stat_id[0].loss + ((stat_loss - stat_id[0].loss) / stat_sample),
                        avg_median = stat_id[0].median + ((stat_median - stat_id[0].median) / stat_sample),
                        avg_min = stat_id[0].min + ((stat_min - stat_id[0].min) / stat_sample),
                        avg_max = stat_id[0].max + ((stat_max - stat_id[0].max) / stat_sample),
                        avg_stdev = stat_id[0].stdev + ((stat_stdev - stat_id[0].stdev) / stat_sample)
                    )
            
            # Update last_change row if pings not 100% successful.
            if (stat_id[0].loss != stat_loss) and ((stat_loss == stat_pings) or (stat_loss == 0)):
                stat.objects.filter(id=stat_id[0].id).update(
                    last_change=now()
                )

            # Update Host RRD
            rrd_fping(agent_id, fping_row['host'], fping_row['result'])

        return HttpResponse(request)
    
    else:
        return HttpResponse("nothing to do")

#@login_required
def fping_collector(request):
    return FileResponse(open('fping/fping_agent.py', 'rb'))

#@login_required
def graph_host(request, agent_id, address_id):

    if 'start' in request.GET:
        html_start = request.GET['start']
        rrd_start = datetime.strptime(request.GET['start'], '%Y-%m-%dT%H:%M').strftime("%s")
    else:
        html_start = (datetime.now()-timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M")
        rrd_start = (datetime.now()-timedelta(hours=9)).strftime("%s")

    if 'end' in request.GET:
        html_end = request.GET['end']
        rrd_end = datetime.strptime(request.GET['end'], '%Y-%m-%dT%H:%M').strftime("%s")
    else:
        html_end = datetime.now().strftime("%Y-%m-%dT%H:%M")
        rrd_end = datetime.now().strftime("%s")

    fping_rrds = []
    for host_row in host.objects.values('enabled','address','hostname','agent').filter(address__exact=address_id):

        if agent.objects.values('active').get(agent=host_row['agent']):
            fping_rrds.append([host_row['agent'],host_row['address'],host_row['hostname']])

        if str(host_row['agent']) == str(agent_id):
            fping_hostname = host_row['hostname']
            fping_rrd = [host_row['agent'],host_row['address'],host_row['hostname']]

    return render(request, 'fping/graph.html', {
        'agent': agent_id,
        'address': address_id,
        'hostname': fping_hostname,
        'start': html_start,
        'end': html_end,
        'graph': rrd_graph.smoke(fping_rrd, rrd_start, rrd_end),
        'multi': rrd_graph.multi(fping_rrds, rrd_start, rrd_end)
    })