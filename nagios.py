"""

 REV SOFTWARE CONFIDENTIAL

 [2013] - [2016] Rev Software, Inc.
 All Rights Reserved.

 NOTICE:  All information contained herein is, and remains
 the property of Rev Software, Inc. and its suppliers,
 if any.  The intellectual and technical concepts contained
 herein are proprietary to Rev Software, Inc.
 and its suppliers and may be covered by U.S. and Foreign Patents,
 patents in process, and are protected by trade secret or copyright law.
 Dissemination of this information or reproduction of this material
 is strictly forbidden unless prior written permission is obtained
 from Rev Software, Inc.

"""

import settings
import requests
import logging
from pprint import pprint,pformat
import json

logger = logging.getLogger('Nagios')
logger.setLevel(logging.DEBUG)

class Nagios():
    BASE_URL = settings.NAGIOS_URL

    def _api_call(self, relative_url, method="GET", data=None):
        url = "%s%s" % (self.BASE_URL,relative_url)
        logger.debug("API call %s %s" % (method, url))    
        headers = {
            'Content-Type': 'application/json',
        }    
        if method == "GET":
            if data is  None: 
                response = requests.get(url, headers=headers)
            else:
                response =  requests.get(url, data=json.dumps(data), headers=headers)
        elif method == "POST":
            if data is  None: 
                response = requests.post(url, headers=headers)
            else:
                response =  requests.post(url, data=json.dumps(data), headers=headers)
        else:
            raise Exception("Unknown method type")
        
        response_data = json.loads(response.content)
        
        if not response_data['success']:
            logger.error("nagios response not set with success flag:\n%s" % pformat(response_data))
            raise Exception("response success is not set.")
        
        if response.status_code != 200:
            logger.error("nagios response with status code %d:\n%s" % (response.status_code, pformat(response_data)))
            raise Exception("nagios response status-code %d" % response.status_code)
        
        return response_data['content']
            
    def _get_api_call(self, relative_url, data=None):
         return self._api_call(relative_url,"GET", data)

    def _post_api_call(self, relative_url, data=None):
         return self._api_call(relative_url,"POST", data)
    
    def get_state(self):
        return self._get_api_call('state')
    
    def schedule_downtime(self, server, duration=1200):
        logger.info("declaring scheduled downtime on %s for %d seconds" % (server, duration))
        data = {
            'host': server,
            'duration': duration,
        }
        self._post_api_call("schedule_downtime", data)
        
    def cancel_downtime(self, server):
        logger.info("Canceling downtime on %s" % server)
        data = {
            'host': server,
        }
        self._post_api_call("cancel_downtime", data)
        
#     def get_monitoring_jobs(self):
#          return self._get_api_call("/v1/monitoring/jobs")
#     
#     def get_monitoring_job_by_host(self, host):
#         logger.debug("Looking for the nsone monitoring job of host %s" % host)
#         for job in self.get_monitoring_jobs():
#             if job['config']['host'].lower() == host.lower():
#                 logger.debug("The nsone monitoring job of host %s is %s" % (host,job['id']))
#                 return job
#         raise Exception("Could not find monitoring job for host %s" % host)
#              
#     def fail_monitoring_job(self, host):
#         logger.debug("Failing monitoring job for server %s" % host)
#         monitoring_job = self.get_monitoring_job_by_host(host)
#         job_id = monitoring_job['id']
#         data = {
#             'rules': [
#                 {
#                     'comparison': 'contains',
#                     'key': 'output',
#                     'value': 'Fail on purpose, server in in maintenance'
#                 }
#         ]}
#         self._post_api_call("/v1/monitoring/jobs/%s" % job_id, data)
#     
#     def unfail_monitoring_job(self, host):
#         logger.debug("Unfailing monitoring job for server %s" % host)
#         monitoring_job = self.get_monitoring_job_by_host(host)
#         job_id = monitoring_job['id']
#         data = {
#             'rules': [
#                 {
#                     'comparison': 'contains',
#                     'key': 'output',
#                     'value': 'this is a test'
#                 }
#         ]}
#         self._post_api_call("/v1/monitoring/jobs/%s" % job_id, data)
