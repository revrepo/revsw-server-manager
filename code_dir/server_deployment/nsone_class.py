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


class Ns1Deploy():

    def __init__(self, host_name, host, logger):
        self.host_name = host_name
        self.host = host

        self.logger = logger
        self.ns1 = NSONE(apiKey=settings.NSONE_KEY)
        self.monitor = self.ns1.monitors()

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
        logger.info('Finding monitor  in ns1 by hostname')
        monitors = self.get_monitor_list()
        for monitor in monitors:
            if monitor['name'] == self.host_name:
                logger.info('Monitor founded its id %s' % monitor['id'])
                return monitor['id']
        return False

    def add_new_monitor(self):
        monitor_data = {
            "region_scope": "fixed",
            "frequency": 20,
            "rapid_recheck": False,
            "policy": "quorum",
            "notify_delay": 0,
            "notify_repeat": 0,
            "notify_failback": True,
            "notify_regional": False,
            "rules": [
                {
                    "key": "output",
                    "comparison": "contains",
                    "value": "this is a test"}
            ],
            "regions": ["sjc", "sin", "lga"],
            # "regions": ["sjc",],
            "job_type": "tcp",
            "config": {
                "response_timeout": 1000,
                "connect_timeout": 2000,
                "host": self.host_name,
                "port": 80,
                "send": "GET /test-cache.js HTTP/1.1\nHost: monitor.revsw.net\n\n"
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
            }, "ns1")
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
        logger.info("Deleting monitor from NS1")
        try:
            monitor = self.monitor.delete(monitor_id)
        except ResourceException as e:
            log_error = e.message
            raise DeploymentError(log_error)
        logger.info("Monitor deleted")
        return monitor

    def get_zone(self, zone_name):
        try:
            zone = self.ns1.loadZone(zone_name)
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

    def add_a_record(self, zone, short_name):
        try:
            record = zone.add_A(short_name, [self.host])
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

    def get_a_record(self, zone, domain, record_type):
        try:
            logger.info(
                    "Checkig if record already exist get by zone %s, domain %s, record_type %s" %
                    (zone, domain, record_type)
                )
            record = Record(zone, domain, record_type)
            record.load()
        except ResourceException as e:
            if e.message == 'server error: record not found':
                return
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
            logger.info(
                'Adding new data feed to NS1 to monitor %s and data source %s' % (monitor_id, source_id)
            )
            feedAPI = self.ns1.datafeed()
            feed = feedAPI.create(
                source_id,
                "%s status" % self.host_name,
                config={"jobid": monitor_id}
            )
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
        logger.info('New feed succesfully added  feed id %s' % feed['id'])
        return feed

    def find_feed(self, source_id, monitor_id):
        logger.info(
            "Finding in NS1 data feed  by monitor %s in data source %s" % (monitor_id, source_id)
        )
        try:
            feedAPI = self.ns1.datafeed()
            feed_list = feedAPI.list(source_id)
            for feed in feed_list:
                if feed['config']['jobid'] == monitor_id:
                    feed_id = feed['id']
                    logger.info('feed was found, its id %s' % feed_id)
                    return feed_id
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
        logger.info('Feed was not found')
        return None

    def delete_feed(self, source_id, monitor_id):
        logger.info("Deleting data feed")
        try:
            feedAPI = self.ns1.datafeed()
            feed_id = self.find_feed(source_id, monitor_id)
            if not feed_id:
                return
            feedAPI.delete(source_id, feed_id)
            logger.info("Feed succesfuly deleted")
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

    def add_answer(self, zone, record_name, record_type, answer_host, region, feed_id):
        answer_data = {
            'answer': [answer_host],
            'region': region,
            'meta': {
                "priority": 1,
                "up": {'feed': feed_id}
            }
        }
        try:
            record = self.ns1.loadRecord(record_name, record_type)
            if not record:
                logger.info(' A dns balance record not found')
                return
            logger.info("Checking if answer already exist")
            for answer in record.data['answers']:
                if answer['answer'] == [answer_host]:
                    logger.info("Answer already exist")
                    return
            logger.info("Answer not found. Adding new answer")
            record.addAnswers([answer_data])
            logger.info("Answer succesfully added")

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
