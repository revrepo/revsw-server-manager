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
from nsone.records import Record
from nsone.rest.errors import ResourceException
from nsone.zones import ZoneException

import settings
from nsone import NSONE

from server_deployment.utilites import DeploymentError


class NsOneDeploy():

    def __init__(self, host_name, host, logger):
        self.host_name = host_name
        self.host = host

        self.logger = logger
        self.nsone = NSONE(apiKey=settings.NSONE_KEY)
        self.monitor = self.nsone.monitors()
        # self.zone = self.nsone.
        # print(zone)
        # record = zone.add_A('honey', ['1.2.3.4', '5.6.7.8'])
        # print(record)


    def add_new_monitor(self):
        monitor_data = {
            "name": self.host_name,
            "job_type": "tcp",
            "region_scope": "fixed",
            "regions":["ams"],
            "frequency":60,
            "config": {"host":self.host, "port": 80},
            "rules": [
                {"key":"output", "comparison":"contains", "value":"200 OK"}
            ],
        }
        try:
            monitor = self.monitor.create(monitor_data)
        except ResourceException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'no',
                "monitored": 'fail',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)

        self.logger.log({
                "host_added": 'no',
                "monitored": 'yes',
            }, "nsone")
        return monitor['id']

    def get_zone(self, zone_name):
        try:
            zone = self.nsone.loadZone(zone_name)
        except ResourceException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)
        except ZoneException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)

        return zone

    def add_record(self, zone):
        try:
            record = zone.add_A('honey', [self.host])
        except ResourceException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)
        except ZoneException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)

        return record

    def get_record(self, zone, domain, type):
        try:
            record = Record(zone, domain, type)
        except ResourceException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)
        except ZoneException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)

        return record

