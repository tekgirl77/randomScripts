#!/bin/env python

'''
This Nagios check script will return Sentry event counts for each Django
client per the default thresholds or passed as args.
Sentry API Reference:
 https://docs.sentry.io/api/
'''

import requests
from datetime import datetime, timedelta
import logging
import optparse as opt
import sys
from collections import Counter

url = 'http://sentry-onpremise.example.com'
token = 'your sentry auth token here'
headers = {'Authorization': 'Bearer {0}'.format(str(token)), 'Content-Type': 'application/json'}

# Standard Nagios return codes
OK       = 0
WARNING  = 1
CRITICAL = 2
UNKNOWN  = 3


def end(status, message):
    """
    Prints a message and exits.
    First arg is the status code.
    Second Arg is the string message.
    """
    check_name = "500Errors"
    if status == OK:
        print("{0} OK - {1}".format(str(check_name), str(message))),
        sys.exit(OK)
    elif status == WARNING:
        print("{0} WARNING - {1}".format(str(check_name), str(message))),
        sys.exit(WARNING)
    elif status == CRITICAL:
        print("{0} CRITICAL - {1}".format(str(check_name), str(message))),
        sys.exit(CRITICAL)
    else:
        # This one is intentionally different
        print("UNKNOWN - {0}".format(str(message))),
        sys.exit(UNKNOWN)


parser = opt.OptionParser()
parser.add_option("-w", "--warn", action="store", dest="warn",
                  help="Warning threshold, default=10", metavar="WARN", default=10, type="int")
parser.add_option("-c", "--crit", action="store", dest="crit",
                  help="Critical threshold, default=50", metavar="CRIT", default=50,type="int")
parser.add_option("-t", "--time", action="store", dest="time",
                  help="How far back to check in seconds, default=300", metavar="TIME", default=300,type="int")
parser.add_option("-s", "--site", action="store", dest="site",
                  help="The sentry site to check (i.e. AK client)", metavar="SITE")
parser.add_option("-l", "--level", action="store", dest="level",
                  help="Logging level to report on, default='ERROR'", default='ERROR', metavar="LEVEL")
(options, args) = parser.parse_args()

if not options.site:
    print "Need to name a site (client)."
    parser.print_help()
    sys.exit()

level = getattr(logging, options.level)

# Get org slugs
orgs = requests.get('{0}/api/0/organizations/'.format(str(url)), headers=headers)
org_slugs = []
for org in orgs.json():
    org_slugs.append(org['slug'])

since = (datetime.utcnow() - timedelta(seconds=options.time)).strftime('%s')
# Get projects for each org
for org in org_slugs:
    projects = requests.get('{0}/api/0/organizations/{1}/projects/'.
                            format(str(url), str(org)), headers=headers)
    # Check total events for each project since the time specified (default=300 seconds)
    for project in projects.json():
        event_count = requests.get('{0}/api/0/projects/{1}/{2}/stats/?since={3}'.
                                   format(str(url), str(org), str(project['slug']), str(since)), headers=headers)
        total_events = sum(int(i[1]) for i in event_count.json())
        if total_events > 0:
            counts = Counter()
            project_events = requests.get('{0}/api/0/projects/{1}/{2}/events/'.
                                          format(str(url), str(org), str(project['slug'])), headers=headers)
            # Determine AK client and event count
            for event in project_events.json():
                site = None
                tags = event['tags']
                # Look for the 'site' tag in event to determine AK client
                for dict, key in enumerate(d['key'] for d in tags):
                    if key == 'site':
                        site = str(tags[dict]['value'])
                dateReceived = datetime.strptime((event['dateReceived']), '%Y-%m-%dT%H:%M:%SZ').strftime('%s')
                if site == str(options.site) and dateReceived >= since:
                    group_id = (event['groupID'])
                    counts[group_id] += 1
            most_common = counts.most_common(1)
            group, count = most_common[0] if most_common else (0, 0)

            if count >= options.crit:
                end(CRITICAL, "Most common 500 error occurred {0} times in the last {1} seconds: "
                              "{2}/{3}/{4}/issues/{5}/".
                    format(str(count), options.time, str(url), str(org), str(project['slug']), str(group)))
            elif count >= options.warn:
                end(WARNING, "Most common 500 error occurred {0} times in the last {1} seconds: "
                             "{2}/{3}/{4}/issues/{5}/".
                    format(str(count), options.time, str(url), str(org), str(project['slug']), str(group)))
            else:
                end(OK, "500 errors occurred {0} times in the last {1} seconds: "
                        "{2}/{3}/{4}/issues/{5}/".
                    format(str(count), options.time, str(url), str(org), str(project['slug']), str(group)))
