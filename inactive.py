# Name: inactive.py
# Purpose: script to dump inactive registered Cb Defense endpoint
# Version: 0.1.1
# Last Update 2020-01-05
#
# Update History
# 0.1.0 - initial release
# 0.1.1 - added override inactive dates feature
#
# Author: Steve Chan
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
# Input file: apikey.txt
# 				Contain an custom API credential (API Secret key/API ID), Org Key and Org ID
#
# Output file: inactivedevice.csv
#				Contain list of endpoints last contact day less than the inactive threshold
#
# Reference: https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/
# Reference section: Search Devices
#
# Notes:
# inactive threshold is default to 90 days
# CB API query maximum row is capped per API call
# the limit is set in variable inc_cnt with a value of 30000
# if the query returned with an 400 error then reduce the limit
#
# Usage example:
# inactive.py - dump all registered endpoints with last communication date less than 90 days from today
# inactive.py 60 - dump all registered endpoints with last communication date less than 60 days from today

import os
import sys
import csv
import requests
import json
from datetime import datetime, timedelta

inactive_threshold = 90
count = 0
inc_cnt = 30000
start_count = 0
rows_count = 0

if len(sys.argv) == 1:
	print ('No inactive threshold override. Default to 90 days')
else:
	try: threshold = int(sys.argv[1])
	except ValueError:
		print ('Override is not a number. Override >'+sys.argv[1]+'< found')
		sys.exit()
	if threshold < 0:
		print ('Inactive overide is negative value. Aborting run')
		sys.exit()
	if threshold < 30:
		print ('\n' + '*** Warning ***' + '\n' + 'Override inactive threshold is less than 30 days')
		print ('Endpoints list may contains active endpoints in storage')
		print ('Please execise caution when removing endpoints from the list'+ '\n' + '*** Warning ***' + '\n')
	inactive_threshold = threshold
	print ('Threshold override found. Changing inactive threshold to ' + str(inactive_threshold) + ' days')

inactive_datetime = str(datetime.now() - timedelta(days=inactive_threshold))
inactive_date = inactive_datetime[:10]
print ('Today date: ' + str(datetime.now())[:10] + ', inactive date: ' + inactive_date)
inactive_date = inactive_date.replace('-','')[:8]

# read keys info
with open('apikey.txt') as apikeyfile:
	apikey = csv.reader(apikeyfile, delimiter=',')
	for row in apikey:
#		print("API Key (x-auth-token, org_key, org_id): ", row)
		x_auth_token = row[0]
		org_key = row[1]
		org_id = row[2]

auth_header = {'X-Auth-Token': x_auth_token}

data = {"criteria": {"status": ["REGISTERED"], },"start":0,"rows":0}
print ('Chekcing number of devices in inventory')
url_export = "https://defense-prod05.conferdeploy.net/appservices/v6/orgs/" + org_key + "/devices/_search"
#print ('url:', url_export)
response = requests.post(url_export,headers=auth_header, json=data)
#print ('Download return code:', response.status_code)
if response.status_code != 200:
	print ('Invalid query')
	print (data)
	sys.exit()
json_data = response.json()
print ('Total registered endpoints found:', json_data['num_found'])
loop_cnt = int(int(json_data['num_found']) / inc_cnt)
loop_last = int((json_data['num_found'])%(inc_cnt * loop_cnt))
#print ('Number of loop:', loop_cnt, 'last loop rows:',loop_last)

print ('Searching for inactive device with last communication date earlier than', inactive_date)

with open('inactivedevices.csv', 'w', newline = '') as f:
	f.write('Device_Id,Device_Name,Inactive_date,Last_communication_date,Sensor_Version' + '\n')
	if loop_cnt > 0:
		for read_loop in range (0,loop_cnt):
			data = {"criteria": {"status": ["REGISTERED"]},"start":start_count,"rows":inc_cnt}
			print ('Searching', inc_cnt, 'devices from position', start_count)
			response = requests.post(url_export,headers=auth_header, json=data)
			json_data = response.json()
			for device in json_data['results']:
				last_contact_time = device.get('last_contact_time')
				last_contact = last_contact_time.replace('-', '')[:8]
				if (int(last_contact) < int(inactive_date)):
					h_id = device.get('id')
					h_name = device.get('name')
					h_last_comm = device.get('last_contact_time')
					h_sensor_ver = device.get('sensor_version')
					name = str(h_id) + ',' + str(h_name) + ',' + str(inactive_date) + ',' + str(h_last_comm) + ',' + str(h_sensor_ver) + '\n'
					count += 1
					f.write(name)
			start_count = start_count + inc_cnt + 1
			print('Found', count, 'inactive devices')
	print ('Searching', loop_last, 'devices from position', start_count)
	data = 	 {"criteria": {"status": ["REGISTERED"]},"start":start_count,"rows":loop_last}
	response = requests.post(url_export,headers=auth_header, json=data)
	json_data = response.json()
	for device in json_data['results']:
		last_contact_time = device.get('last_contact_time')
		last_contact = last_contact_time.replace('-', '')[:8]
		if int(last_contact) < int(inactive_date):
			h_id = device.get('id')
			h_name = device.get('name')
			h_last_comm = device.get('last_contact_time')
			h_sensor_ver = device.get('sensor_version')
			name = str(h_id) + ',' + str(h_name) + ',' + str(inactive_date) + ',' + str(h_last_comm) + ',' + str(h_sensor_ver) + '\n'
			count += 1
			f.write(name)
	print ('Found', count, 'inactive devices')
