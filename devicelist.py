# Name: devicelist.py
# Purpose: Script to dump Cb Defense endpoint list in CSV format
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
# Version: 0.1.1
# Last Update 2020-01-02
#
# Update History:
# 0.1.1 - Added override search feature
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
# Reference: https://developer.carbonblack.com/reference/carbon-black-cloud/platform/latest/devices-api/
# Reference section: Export Devices (CSV)
#
# Notes:
# search parameters are case insensitive
# search status default to "ALL".
# Other valid value: PENDING, REGISTERED, UNINSTALLED, DEREGISTERED,
#					 ACTIVE, INACTIVE, ERROR, BYPASS_ON, BYPASS,
#					 QUARANTINE, SENSOR_OUTOFDATE, DELETED, LIVE
#
# Usage example:
# devicelist.py - dump all endpoints
# devicelist.py all -  dump all endpoints
# devicelist.py inactive - dump only inactive endponts

import os
import sys
import csv
import requests

search_status = 'all'
device_count = 0

search_list = ['ALL','PENDING','REGISTERED','UNINSTALLED','DEREGISTERED','ACTIVE','INACTIVE','ERROR','BYPASS_ON','BYPASS','QUARANTINE','SENSOR_OUTOFDATE','DELETED','LIVE']

if len(sys.argv) == 1:
	print ('No overrided search argument entered. Default to search ALL devices')
elif str.upper(sys.argv[1]) in search_list:
	search_status = str.lower(sys.argv[1])
	print ('Override search argument found. Changing search argument to search >' + search_status + '<')
else:
	print ('Invalid override search argument found. Seach argument entered is >' + str(sys.argv[1]) + '<' + '\n')
	print ('Valid search argument: ALL | PENDING | REGISTERED | UNINSTALLED |')
	print ('                       DEREGISTERED | ACTIVE |INACTIVE | ERROR | BYPASS_ON |')
	print ('                       BYPASS | QUARANTINE | SENSOR_OUTOFDATE | DELETED | LIVE' + '\n')
	print ('Default search to ALL when no argument passed')
	sys.exit()

# read keys file
with open('apikey.txt') as apikeyfile:
    apikey = apikeyfile.read().split(",")
    x_auth_token = apikey[0]
    org_key = apikey[1]
    org_id = apikey[2]
apikeyfile.close()
auth_header = {'X-Auth-Token': x_auth_token}

output_file = str.lower(search_status) + '-devices.csv'
output_file_directory = os.getcwd()

# query through API
print ('Downloading '+ search_status + ' devices from CB')
url = "https://defense-prod05.conferdeploy.net/appservices/v6/orgs/"+org_key+"/devices/_search/download?status="+search_status
response = requests.get(url,headers=auth_header)
print ('Download return code:', response.status_code)

# write result to file when query completed successfuly
if response.ok:
	print ('Download completed successfully')
	print ('Writing devices list to file ' + output_file + ' in folder ' + output_file_directory)
	with open(output_file, 'w', newline = '') as f:
		writer = csv.writer(f)
		for line in response.iter_lines():
			writer.writerow(line.decode('utf-8').replace('"','').split(','))
			device_count += 1
		print (str(device_count) + ' devices written to file successfully')
elif response.status_code == 400:
	print ('Invalid request')
elif response.status_code == 401:
	print ('Invalid API authentication key. Please validate the API key have proper role')
	print ('Authentication key used: >' + x_auth_token + '<')
elif response.status_code == 404:
	print ('Invalid org_key. Please validate the organization key')
	print ('Organization key used: >' + org_key + '<')
elif response.status_code == 500:
	print ('CB Internal Server Error. Please wait and retry')
else:
	print ('Undefined error')
	print (respons.text)
