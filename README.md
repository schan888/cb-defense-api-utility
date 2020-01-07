# Cb Defense API Utilities

alerts.py - retrieve list of "policy applied" alerts based on a time window. 
  Usage example: 
  alerts.py - retrieve last calendar month's event_start,
  alert.py 2019-10-01 - retrieve 30 days of event from 2019-10-01,
  alert.py 2019-11-01 1019-11-10 - retrieves events between 2019-11-01 to 2019-11-10 inclusive.

bulkderegister.py - bulk delete a list of endpoints with no checking.

deregister.py - delete a list of endpoints with last communication date check.

devicelist.py - dump list of registered endpoints matching a status. 
  Usage example: 
  devicelist.py - dump all endpoints, 
  devicelist.py all -  dump all endpoints, 
  devicelist.py inactive - dump only inactive endpoints.

inactive.py - dump list of endpoints based on last communication date. 
  Usage example: 
  inactive.py - dump all registered endpoints with last communication date less than 90 days from today, 
  inactive.py 60 - dump all registered endpoints with last communication date less than 60 days from today.

All script requires an API key file.
Content format: <api_secret_key>/<api_id>,<org_key>,<org_id>
e.g. ABCDEF1234/ABC123,DEF123,1234

Refer to Carbon Black document for detail how to obtain the API key and credentials
https://developer.carbonblack.com/reference/carbon-black-cloud/authentication/

# ***** Warning *****
Keep the API key file secret. Disclosure of the API keys could result unauthorized access to the Cb Defense console
