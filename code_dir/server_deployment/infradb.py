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

import json
from urlparse import urljoin

import requests

import settings
from server_deployment.utilites import DeploymentError


class InfraDBAPI():

    def __init__(self, logger):
        self.logger = logger
        self.session = requests.Session()
        self.session.auth = (settings.INFRADB_USERNAME, settings.INFRADB_PASSWORD)
        self.url = settings.INFRADB_URL

    def add_server(self, host_name, ip, server_versions, location_name, hosting_name):
        location = self._get_location(location_name)
        hosting = self._get_hosting(hosting_name)
        server_data = {
                "name": host_name,
                "status": 'ONLINE',
                "location": location['id'],
                "hostingprovider": hosting['id'],
                "type": 1,
                "IP": ip,
            }
        server_data.update(server_versions)
        response = self.session.post(urljoin(self.url, 'server/'), data=server_data)
        if response.status_code != 201:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"fw": "fail", "log": log_error}, "infraDB")
            raise DeploymentError(log_error)
        self.logger.log({"fw": "ok"}, "infraDB")

    def _get_location(self, location_name):
        response = self.session.get(
            urljoin(self.url, 'location?code=%s' % location_name)
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"fw": "fail", "log": log_error}, "infraDB")
            raise DeploymentError(log_error)
        locations = json.loads(response.content)
        if not locations:
            log_error = "Server error. Wrong location code. Location not found"
            self.logger.log({"fw": "fail", "log": log_error}, "infraDB")
            raise DeploymentError(log_error)
        return locations[0]

    def get_server(self, server_name):
        response = self.session.get(urljoin(self.url, 'server/'), name=server_name)
        if response.status_code == 200:
            return response.text
        elif response.status_code == 404:
            return None
        else:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            raise DeploymentError(log_error)

    def _get_hosting(self, provider_name):
        response = self.session.get(
            urljoin(self.url, 'hosting?name=%s' % provider_name)
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"fw": "fail", "log": log_error}, "infraDB")
            raise DeploymentError(log_error)
        hostings = json.loads(response.content)
        if not hostings:
            log_error = "Server error. Wrong hosting provider name. Hosting provider not found"
            self.logger.log({"fw": "fail", "log": log_error}, "infraDB")
            raise DeploymentError(log_error)
        return hostings[0]