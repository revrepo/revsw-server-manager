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
import logging

from nsone.records import Record
from nsone.rest.errors import ResourceException
from nsone.zones import ZoneException

import settings
from nsone import NSONE

from server_deployment.utilites import DeploymentError


logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)

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


    def get_monitor_list(self):
        try:
            monitors = self.monitor.list()
        except ResourceException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'no',
                "monitored": 'fail',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)
        return monitors

    def check_is_monitor_exist(self):
        logger.info('Cheking  monitors list if server already have monitor')
        monitors = self.get_monitor_list()
        for monitor in monitors:
            if monitor['name'] == self.host_name:
                logger.info("monitor already exist with id %s" % monitor['id'])
                return monitor['id']
        return False


    def add_new_monitor(self):
        monitor_data = {
            "region_scope":"fixed",
            "frequency":20,
            "rapid_recheck":False,
            "policy":"quorum",
            "notify_delay":0,
            "notify_repeat":0,
            "notify_failback":True,
            "notify_regional":False,
            "rules":[
                {"key":"output","comparison":"contains","value":"this is a test"}
            ],
            "regions":["sjc","sin","lga"],
            "job_type":"tcp",
            "config":{
                "response_timeout":1000,
                "connect_timeout":2000,
                "host":self.host_name,
                "port":80,
                "send":"GET /test-cache.js HTTP/1.1\nHost: monitor.revsw.net\n\n"
            },
            "name": self.host_name,
            "notify_list": settings.NS1_NOTIFY_LIST_ID
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

    def check_monitor_status(self, monitor_id):
        monitor = self.get_monitor(monitor_id)
        return monitor["status"]["global"]["status"]

    def get_monitor(self, monitor_id):
        try:
            monitor = self.monitor.retrieve(monitor_id)
        except ResourceException as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'no',
                "monitored": 'fail',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)
        return monitor

    def delete_monitor(self, monitor_id):
        try:
            monitor = self.monitor.delete(monitor_id)
        except ResourceException as e:
            log_error = e.message
            raise DeploymentError(log_error)
        return monitor

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
        logger.info("Zone id %s" % zone['id'])
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

    def get_record(self, zone, domain, record_type):
        try:
            record = Record(zone, domain, record_type)
            record.load()
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

    def add_feed(self, source_id, monitor_id):
        try:
            feedAPI = self.nsone.datafeed()
            feed = feedAPI.create(source_id,
                                   "%s status" % self.host_name,
                                   config={"jobid": monitor_id})
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
        except Exception as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)

        return feed

    def add_answer(self, zone, record_name, record_type, answer_host):
        try:
            record = self.nsone.loadRecord(record_name, record_type)
            record.addAnswers(answer_host)

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
        except Exception as e:
            log_error = e.message
            self.logger.log({
                "host_added": 'fail',
                "monitored": 'yes',
                "log": log_error
            }, "infraDB")
            raise DeploymentError(log_error)