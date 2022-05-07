#!/bin/env python3

"""
fping agent collector for django server.
"""

from json import dumps, loads
from subprocess import Popen, PIPE
from requests import session

URL = "http://cafe.crc1.net:8000/agent/CAFE"

def probe_fping(opts, targets):

    """
    Run fping command & return json string with results.
    """

    fping_cmd = [ 'fping' ]
    fping_cmd += list(opts)
    fping_cmd += list(targets)

    fping_output = Popen(fping_cmd, stderr=PIPE).communicate()[1].decode("utf-8").splitlines()

    result_string = {}
    result_string['probe'] = 'fping'
    result_string['target'] = []

    for index, line in enumerate(fping_output, 0):

        for idx, col in enumerate(line.split(), -1):
            if idx > 0:
                if col == '-':
                    result_string['target'][index]['result'].append(None)
                else:
                    result_string['target'][index]['result'].append(float(col))
            elif idx < 0:
                result_string['target'].append({})
                result_string['target'][index]['host'] = col
                result_string['target'][index]['result'] = []

    return result_string

if __name__ == '__main__':

    POST = {}
    POST['data'] = []

    client = session()
    GET = client.get(URL)

    # Fetch CSFR token from server.
    if 'csrftoken' in GET.cookies:
        csrftoken = GET.cookies['csrftoken']

    fping_job = loads(GET.text)

    if fping_job['probe'] == 'fping':
        POST['data'].append(
                probe_fping(
                    fping_job['opts'],
                    fping_job['targets']
                )
        )

#   post_data = dict(csrfmiddlewaretoken=csrftoken, data=dumps(POST))
    post_data = dict(data=dumps(POST))
    submit = client.post(URL, data=post_data).status_code

    if submit == 200:
        print(dumps(POST))
