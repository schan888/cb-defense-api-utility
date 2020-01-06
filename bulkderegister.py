# Name: bulkderegister.py
# Purpose: Script to bulk remove inactive devices through Carbon Black Cloud Devices API
# Version: 0.1.0
# Last Update: 2020-01-05
#
# Update history:
# 0,1.0 - initial release
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
# Input files:
#	apikey.txt - Contain CB Defense API credentials
#		Content format: "<api_secret_key>/<api_id>","<org_key","org_id"
# 	inactive-device.csv - Contain a list of inactive endpoints to remove
#		content format: <device>,<hostname>,<inactive_date_cutoff_date>,<last_contact_date>,<sensor_version>
#
# Output file:
#	bulkderegister-result.csv - Contain result of the bulk removal operation
#		content format: <delete_result>,<[hostname1-hostname2-.....]
#
# Reference: https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/
# Reference section: Device Actions
#
# Notes:
# CB API could return a failed result if one or or more deregistraton failed
# but this does not mean the deletion of the the whole batch failed
# CB might might throttle API call and might caused deregistration failure
# Use with caution as there is no check of whether a device is back online before deregistration

import sys
import csv
import requests
import json
import time

count = 0
batch = 0
batch_max = 50
devices_list = []
dev_list = ''

# Need to uninstall before delete
# Note: 2019-12-31 there is a discrepancy on the API document. DEREGISTER_SENSOR is an invalid action and should be UNINSTALL_SENSOR
def remove_device(device_list):
	url_action = "https://defense-prod05.conferdeploy.net/appservices/v6/orgs/" + org_key + "/device_actions"
	data = {'action_type': 'UNINSTALL_SENSOR', 'device_id': device_list}
	response = requests.post(url_action,headers=auth_header,json=data)
	if response.status_code == 204:
		time.sleep(5)
		data = {'action_type': 'DELETE_SENSOR', 'device_id': device_list}
		response = requests.post(url_action,headers=auth_header,json=data)
		if response.status_code != 204:
			response.status_code = 402
	else:
		response.status_code = 401
	return (response.status_code)

# read keys info
with open('apikey.txt') as apikeyfile:
	apikey = csv.reader(apikeyfile, delimiter=',')
	for row in apikey:
		print("API Key (x-auth-token, org_key, org_id): ", row)
		x_auth_token = row[0]
		org_key = row[1]
		org_id = row[2]

auth_header = {'X-Auth-Token': x_auth_token}

# process delete list file
with open('bulkderegister-result.csv', 'w') as inactive_result:
	with open('inactive-devices.csv') as inactive_list:
		devices = csv.reader(inactive_list, delimiter=',')
		for devices in inactive_list:
			device = devices.split(",")
			device_id = device[0]
			if count == batch_max:
				batch += 1
				print ('Deleting batch', batch, 'of', count, 'endpoints')
				d = remove_device(devices_list)
				if d == 204:
					print ('Batch removed successfuly')
					inactive_result.write('success,'+ dev_list + '\n')
				elif d == 401:
					print ('Batch uninstall failed')
					inactive_result.write('uninstall_failed,'+ dev_list + '\n')
				elif d == 402:
					print ('Batch delete failed')
					inactive_result.write('delete_failed,'+ dev_list + '\n')
				else:
					print ('Batch removal failed with unknown return code: ', d)
					inactive_result.write('unknown_error,'+ dev_list + '\n')
				count = 1
				devices_list = []
				devices_list.append(device_id)
				dev_list = str(device_id)
				time.sleep(10)
			else:
				devices_list.append(device_id)
				count += 1
				if count == 1:
					dev_list = str(device_id)
				else:
					dev_list = dev_list + '-' + str(device_id)
			devices = csv.reader(inactive_list, delimiter=',')
		print ('Deleting last batch batch of', count, 'endpoints')
		d = remove_device(devices_list)
		if d == 204:
			print ('Batch removed successfuly')
			inactive_result.write('success,'+ dev_list + '\n')
		elif d == 401:
			print ('Batch uninstall failed')
			inactive_result.write('uninstall_failed,'+ dev_list + '\n')
		elif d == 402:
			print ('Batch delete failed')
			inactive_result.write('delete_failed,' + dev_list + '\n')
		else:
			print ('Batch removal failed with unknown return code: ', d)
			inactive_result.write('unknown_error,' + dev_list + '\n')
