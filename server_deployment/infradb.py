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


# TODO: here will be infraDB API
from urlparse import urljoin

import requests

from server_deployment.utilites import DeploymentError


class InfraDBAPI():

    def __init__(self, username, password, logger):
        self.logger = logger
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.url = 'http://localhost:8000/api/'

    def add_server(self, server_daata):
        response = self.session.post(urljoin(self.url, 'server/'), data=server_daata)
        if response.status_code != 201:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"fw": "fail", "log": log_error}, "infraDB")
            raise DeploymentError(log_error)
        self.logger.log({"fw": "ok"}, "infraDB")

    def get_locations(self):
        response = self.session.get(urljoin(self.url, 'locations_list/'))
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            raise DeploymentError(log_error)
        return response.text

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

    def get_hosting_providers(self):
        response = self.session.get(urljoin(self.url, 'hosting_list/'))
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            raise DeploymentError(log_error)
        return response.text

