# Name: alerts.py
# Purpose: Script to retrieve Cb Defense endpoint alerts
# Version: 0.1.1
# Last Update 2020-01-05
#
# Update History
# 0.1.0 - initial release
# 0.1.1 - added override dates feature
#
# Copyright (c) 2020 Steve Chan
#
# License:
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Input file:
#	apikey.txt - Contain CB Defense API credentials
#		Content format: <api_secret_key>/<api_id>,<org_key>,<org_id>
#		e.g. ABCDEF1234/ABC123,DEF123,1234
#
# Output file:
#	device_list.csv - Contain list of all registered endpoints
#		contend format: name,email,firstName,lastName,middleName,targetValue,status,registeredTime,deregisteredTime,
#						lastContactTime,lastInternalIpAddress,lastExternalIpAddress,deviceType,policyName,windowsPlatform,
#						osVersion,sensorVersion,avEngine,virtualMachine,virtualizationProvider,macAddress
#
# Reference: https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/alerts-api/
# Reference section: Search Request
#
# Notes:
# Default to regrieve last month's alerts
# To overide the query period, enter the start or start and end dates
# If no override end date provided then retrieve 30 days of events
# Override date format must be yyyy-mm-dd
#
# Usage example:
# alerts.py - retrieve last calendar month's event_start
# alert.py 2019-10-01 - retrieve 30 days of event from 2019-10-01
# alert.py 2019-11-01 1019-11-10 - retrieves events between 2019-11-01 to 2019-11-10 inclusive

import sys
import csv
import requests
import json
import datetime

count = 0
ttps_list = []

def validate(date_text):
    try:
        x = datetime.datetime.strptime(date_text, '%Y-%m-%d')
        date_text = str(x)
    except ValueError:
        date_text = ''
    return(date_text)

today = datetime.date.today()
alert_start = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
alert_end = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
if len(sys.argv) == 1:
	print ('No alert period override. Default to previous month from ', alert_start, 'to ', alert_end)
elif len(sys.argv) == 2:
    arg_start = sys.argv[1]
    print ('Checking override start date:', arg_start)
    r = validate(arg_start)
    if len(r) == 0:
        print ('Invalid alert start date found: >' + arg_start + '<. Accepte only yyyy-dd-mm format')
        sys.exit()
    print ('No override end date found. Default to 30 days')
    alert_start = str(datetime.datetime.strptime(arg_start, '%Y-%m-%d'))[0:10]
    alert_end = str((datetime.datetime.strptime(arg_start, '%Y-%m-%d') + datetime.timedelta(days=30)))[0:10]
else:
    arg_start = sys.argv[1]
    arg_end = sys.argv[2]
    print ('Checking override start date:', arg_start)
    r = validate(arg_start)
    if len(r) == 0:
        print ('Invalid alert start date found: >' + arg_start + '<. Accepte only yyyy-dd-mm format')
        sys.exit()
    print ('Checking override end date:', arg_end)
    r = validate(arg_end)
    if len(r) == 0:
        print ('Invalid alert end date found: >' + arg_end + '<. Accepte only yyyy-dd-mm format')
        sys.exit()
    alert_start = (datetime.datetime.strptime(arg_start, '%Y-%m-%d'))
    alert_end = (datetime.datetime.strptime(arg_end, '%Y-%m-%d'))
    if alert_start > alert_end:
        print('Override start date (' + str(alert_start)[0:10] + ') is greater than override end date (' + str(alert_end)[0:10] + ')')
        sys.exit()
    alert_start = arg_start
    alert_end = arg_end
event_start = str(alert_start) + 'T00:00:00.000Z'
event_end = str(alert_end) + 'T23:59:59.999Z'

# read API and Org info
with open('apikey.txt') as apikeyfile:
    apikey = apikeyfile.read().split(",")
    x_auth_token = apikey[0]
    org_key = apikey[1]
    org_id = apikey[2]
    apikeyfile.close()

auth_header = {'X-Auth-Token': x_auth_token}

# set the event start and end dates
data = {'criteria': {'policy_applied': ['APPLIED'],'create_time': {'start': event_start, 'end': event_end}},'rows': 0}

event_criteria = data['criteria']
event_applied = event_criteria['policy_applied']
event_time = event_criteria['create_time']

print ('search alerts with policy applied status', event_applied)
print ('seearch alert event time:', event_time)

url = "https://defense-prod05.conferdeploy.net/appservices/v6/orgs/" + org_key + "/alerts/cbanalytics/_search"
print ('url:', url)
response = requests.post(url,headers=auth_header, json=data)
if response.status_code == 400:
    print ('Invalid query')
    print (data)
    sys.exit()
json_data = response.json()
print ('Total matching alerts found:', json_data['num_found'])

# set the number of events to retrieve
data['rows'] = json_data['num_found']

response = requests.post(url,headers=auth_header, json=data)
if response.status_code == 400:
    print ('Invalid query')
    print (data)
    sys.exit()
json_data = response.json()
with open('alert_list.csv', 'w') as f:
    f.write('device_name,device_username,policy_name,create_date,create_time_utc,severity,process_name,reason,threat_cause_threat_category,blocked_threat_category,sensor_action,run_state,TTPS,device_id,legacy_alert_id,id' + '\n')
    for alerts in json_data['results']:
        a_ttps = alerts['threat_indicators']
        a_ttps_list = ''
        for ttp in a_ttps:
            a_ttp = ttp['ttps']
            a_ttps_list = a_ttps_list + a_ttp[0] + '|'
        a_detail =  str(alerts['device_name']) + ',' + \
                    str(alerts['device_username']) + ',' + \
                    str(alerts['policy_name']) + ',' + \
                    str(alerts['create_time'][0:10]) + ',' + \
                    str(alerts['create_time'][11:-1]) + ',' + \
                    str(alerts['severity']) + ',' + \
                    str(alerts['process_name']) + ',' + \
                    str(alerts['reason']) + ',' + \
                    str(alerts['threat_cause_threat_category']) + ',' + \
                    str(alerts['blocked_threat_category']) + ',' + \
                    str(alerts['sensor_action']) + ',' + \
                    str(alerts['run_state']) + ',' + \
                    str(a_ttps_list[:-1]) + ',' + \
                    str(alerts['device_id']) + ',' + \
                    str(alerts['legacy_alert_id']) + ',' + \
                    str(alerts['id']) + '\n'
        print ('Device: ', alerts['device_name'], alerts['create_time'][0:10], alerts['create_time'][11:-1])
        count += 1
        try:
            f.write(a_detail)
        except:
            print ('error: ', alerts)
    f.close()
    print ('Written', count, 'alerts events')
