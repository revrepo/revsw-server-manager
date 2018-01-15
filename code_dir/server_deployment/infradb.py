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
import logging
from urlparse import urljoin

import requests

import settings
from server_deployment.utilites import DeploymentError


logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class InfraDBAPI():

    def __init__(self, logger, location_name, hosting_name, ssl_disable=False):
        self.logger = logger
        self.session = requests.Session()
        self.session.auth = (
            settings.INFRADB_USERNAME,
            settings.INFRADB_PASSWORD
        )
        self.url = settings.INFRADB_URL
        self.ssl_verify = not ssl_disable
        self.location = self._get_location(location_name)
        self.hosting = self._get_hosting(hosting_name)

    def add_server(
            self, host_name, ip, server_versions,

    ):
        logger.info("Add server to infradb")
        server_data = {
                "name": host_name,
                "status": 'ONLINE',
                "location": self.location['id'],
                "hostingprovider": self.hosting['id'],
                "type": 7,   # BP Edge proxy
                "IP": ip,
            }
        server_data.update(server_versions)
        response = self.session.post(
            urljoin(self.url, 'server/'),
            data=server_data,
            verify=self.ssl_verify
        )
        if response.status_code != 201:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log(
                {"server_add": "fail", "log": log_error},
                "infraDB"
            )
            raise DeploymentError(log_error)
        self.logger.log({"server_add": "ok"}, "infraDB")
        logger.info("Server succesfuly added to INFRADB")

    def delete_server(self, host_name):
        logger.info("Delete server from infradb")
        server = self.get_server(host_name)

        if not server:
            logger.info("Server not found in infradb")
            return
        server_data = json.loads(server)
        response = self.session.delete(
            urljoin(self.url, 'server/%s' % server_data[0]['id']),
            verify=self.ssl_verify
        )
        if response.status_code != 204:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log(
                {"server_add": "fail", "log": log_error},
                "infraDB"
            )
            raise DeploymentError(log_error)
        # self.logger.log({"server_add": "ok"}, "infraDB")
        logger.info("Server succesfuly deleted from INFRADB")

    def _get_location(self, location_name):
        logger.info("Get location from INFRADB")
        response = self.session.get(
            urljoin(self.url, 'location/?code=%s' % location_name),
            verify=self.ssl_verify
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log(
                {"server_add": "fail", "log": log_error},
                "infraDB"
            )
            raise DeploymentError(log_error)
        locations = json.loads(response.content)
        if not locations:
            log_error = "Server error. Wrong location code. " \
                        "Location not found"
            self.logger.log(
                {"server_add": "fail", "log": log_error},
                "infraDB"
            )
            raise DeploymentError(log_error)
        logger.info(locations[0])
        return locations[0]

    def get_server(self, server_name):
        response = self.session.get(
            urljoin(self.url, 'server/?name=%s' % server_name),
            verify=self.ssl_verify
        )
        if response.status_code == 200:
            if not json.loads(response.text):
                return None
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
            urljoin(self.url, 'hosting/?code=%s' % provider_name),
            verify=self.ssl_verify
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log(
                {
                    "server_add": "fail", "log": log_error
                 },
                "infraDB"
            )
            raise DeploymentError(log_error)
        hostings = json.loads(response.content)
        if not hostings:
            log_error = "Server error. Wrong hosting provider name. " \
                        "Hosting provider not found"
            self.logger.log(
                {"server_add": "fail", "log": log_error},
                "infraDB"
            )
            raise DeploymentError(log_error)
        return hostings[0]
