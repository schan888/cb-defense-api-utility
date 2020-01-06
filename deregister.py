# Name: deregister.py
# Purpose: Script to remove inactive devices through Carbon Black Cloud Devices API
# Version: 0.1.1
# Last Update: 2020-01-06
#
# Update History:
# 0.1.0 - initial release
# 0.1.1 - added logic to check last communication date change
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
# Input files:
#	apikey.txt - Contain CB Defense API credentials
#		Content format: <api_secret_key>/<api_id>,<org_key,org_id
# 	inactive-device.csv - Contain a list of inactive endpoints to remove
#						- export from inactive.py script with the header line removed
#		content format: <device>,<hostname>,<inactive_date_cutoff_date>,<last_contact_date>,<sensor_version>
#
# Output file:
#	inactive-device-result.csv - Contain result of the removal operation
#		content format: <device>,<hostname>,<inactive_date_cutoff_date>,<last_contact_date>,<sensor_version>,<operation_results>
#			operation_results: success | failed-uninstal | failed-deregister | failed-unknown | not_found | already_deleted | last_contact_date_changed
#
# Reference: https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/
# Reference section: Device Actions

import sys
import csv
import requests
import json
import time

def find_device(device_id, last_contact_date):
	url_dev_information = "https://defense-prod05.conferdeploy.net/appservices/v6/orgs/" + org_key + "/devices/" + device_id
	response = requests.get(url_dev_information,headers=auth_header)
	r = response.json()
	if response.ok:
		device_status = r['status']
		device_last_contact = r['last_contact_time']
		if device_status == "DELETED":
			response.status_code = 999
		elif (last_contact_date) != (device_last_contact):
			response.status_code = 888
	return (response.status_code)

# Need to uninstall before delete
# Note: 2019-12-31 there is a discrepancy on the API document. DEREGISTER_SENSOR is an invalid action and should be UNINSTALL_SENSOR
def remove_device(device_id):
	url_action = "https://defense-prod05.conferdeploy.net/appservices/v6/orgs/" + org_key + "/device_actions"
	data = {'action_type': 'UNINSTALL_SENSOR', 'device_id': [device_id]}
	response = requests.post(url_action,headers=auth_header,json=data)
	if response.status_code == 204:
		time.sleep(5)
		data = {'action_type': 'DELETE_SENSOR', 'device_id': [device_id]}
		response = requests.post(url_action,headers=auth_header,json=data)
		if response.status_code != 204:
			response.status_code = 402
	else:
		response.status_code = 401
	return (response.status_code)

# read API and Org info
with open('apikey.txt') as apikeyfile:
    apikey = apikeyfile.read().split(",")
    x_auth_token = apikey[0]
    org_key = apikey[1]
    org_id = apikey[2]
    apikeyfile.close()

auth_header = {'X-Auth-Token': x_auth_token}

# process delete list file
with open('inactive-devices-result.csv', 'w') as inactive_result:
	inactive_result.write('Device_Id,Device_Name,Inactive_date,Last_communication_date,Sensor_Version,Result' + '\n')
	with open('inactive-devices.csv') as inactive_list:
		devices = csv.reader(inactive_list, delimiter=',')
		for devices in inactive_list:
			device = devices.split(",")
			device_id = device[0]
			last_contact_date = device[3]
			device[4] = device[4].replace('\n','')
			r = find_device(device_id, last_contact_date)
			if r == 200:
				d = remove_device(device_id)
				if d == 204:
					print ('Device ' + device_id + ' - hostname ' + device[1] + ' removed')
					device.append('success\n')
				else:
					if d == 401:
						print ('Device ' + device_id + ' - hostname ' + device[1] + ' uninstall failed')
						device.append('failed-uninstall\n')
					elif d == 402:
						print ('Device ' + device_id + ' - hostname ' + device[1] + ' delete failed')
						device.append('failed-deregister\n')
					else:
						print ('Device ' + device_id + ' - hostname ' + device[1] + ' unknown failure')
						device.append('failed-unknown\n')
			elif r == 999:
				print ('Device ' + device_id + ' - hostname ' + device[1] + ' already deleted. Skipped removal')
				device.append('already_deleted\n')
			elif r == 888:
				print ('Device ' + device_id + ' - hostname ' + device[1] + ' last contact date changed. Skipped removal')
				device.append('last_contact_date_changed\n')
			else:
				print ('Device ' + device_id + ' - hostname ' + device[1] + ' not found. Skipped removal')
				device.append('not_found\n')
			result = str(device[0]) + ',' + str(device[1]) + ',' + str(device[2]) + ',' + str(device[3]) + ',' + str(device[4]) + ',' + str(device[5])
			inactive_result.write(result)
			devices = csv.reader(inactive_list, delimiter=',')
