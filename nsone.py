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
import json
import logging

logger = logging.getLogger('NSOne')
logger.setLevel(logging.DEBUG)


class Nsone():
    API_KEY = settings.NSONE_API_KEY
    BASE_URL = "https://api.nsone.net"

    def _api_call(self, relative_url, method="GET", data=None):
        url = "%s%s" % (self.BASE_URL,relative_url)
        logger.debug("nsone api call to %s" % url)
        headers = {
            'X-NSONE-Key': settings.NSONE_API_KEY,
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
            pass
            raise Exception("Unknown method type")
                
        if response.status_code == 200:
            """ success """
            return json.loads(response.content)
        else:
            try:
                response_data = json.loads(response.content)
                message = response_data['message']
            except:
                message = None
     
            if message is None:
                raise Exception("NSONE response status-code %d" % response.status_code)
            else:
                raise Exception("NSONE response status-code %d: %s" % (response.status_code, response_data['message']))

            
    def _get_api_call(self, relative_url, data=None):
         return self._api_call(relative_url,"GET", data)

    def _post_api_call(self, relative_url, data=None):
         return self._api_call(relative_url,"POST", data)
         
    def get_monitoring_jobs(self):
         return self._get_api_call("/v1/monitoring/jobs")
    
    def get_monitoring_job_by_host(self, host):
        logger.debug("Looking for the nsone monitoring job of host %s" % host)
        for job in self.get_monitoring_jobs():
            if job['config']['host'].lower() == host.lower():
                logger.debug("The nsone monitoring job of host %s is %s" % (host,job['id']))
                return job
        raise Exception("Could not find monitoring job for host %s" % host)
             
    def fail_monitoring_job(self, host):
        logger.debug("Failing monitoring job for server %s" % host)
        monitoring_job = self.get_monitoring_job_by_host(host)
        job_id = monitoring_job['id']
        data = {
            'rules': [
                {
                    'comparison': 'contains',
                    'key': 'output',
                    'value': 'Fail on purpose, server in in maintenance'
                }
        ]}
        self._post_api_call("/v1/monitoring/jobs/%s" % job_id, data)
    
    def unfail_monitoring_job(self, host):
        logger.debug("Unfailing monitoring job for server %s" % host)
        monitoring_job = self.get_monitoring_job_by_host(host)
        job_id = monitoring_job['id']
        data = {
            'rules': [
                {
                    'comparison': 'contains',
                    'key': 'output',
                    'value': 'this is a test'
                }
        ]}
        self._post_api_call("/v1/monitoring/jobs/%s" % job_id, data)
