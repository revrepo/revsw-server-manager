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


import unittest
import os
import datetime
from copy import deepcopy

import pymongo

import mongo_logger
import settings

from mock import Mock, patch


TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temporary_testing_files/")


class TestAbstract(unittest.TestCase):
    testing_class = None

    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']
        # print name of running test
        self.testing_class = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        print("RUN_TEST %s" % self._testMethodName)

    def tearDown(self):
        self.mongo_cli.drop_database('test_database')
        # remove all temporary test files
        os.system("rm -r %s" % TEST_DIR)


class TestLoggerClass(TestAbstract):



    test_server_status = {
            "time": datetime.datetime.now().isoformat(),
            "start_time": datetime.datetime.now().isoformat(),
            "host": {
                    "hostname": 'test_host',
                    "ipv4": '127.0.0.1',
                    "ipv6": '2001:db8:3:4::192.0.2.33',
                    "login": "test_login",
                    "password": "test_password",
                    "cert": "test_cert",
                    "reboot": "no",
                    "ping": "no",
                    "udp_port_list": ['8', '8000'],
                    "tcp_port_list": ['8', '8000'],
                    "puppet_installed": 'no',
                    "puppet_configured": 'no',
                    "nagios_installed": 'no',
                    "nagios_configured": 'no',
                    "cacti_installed": 'no',
                    "cacti_configured": 'no',
                    "update": 'no',
                    "upgrade": 'no'
            },
            "hoster": {
                    "api": 'no',
                    "fw": 'off', # [off|proper_set]
                    "udp_port_list": ['8', '8000'],
                    "tcp_port_list": ['8', '8000'],
            },
            "nsone": {
                    "host_added": 'no',
                    "monitored": 'no',
                    "monitor_type": 'dns',
                    "port": 'no',
            },
            "infraDB": {
                    "fw":  'no',
            },
            "revsw": {
                    "revws_repo": 'no',
        },
    }



    def test_validation(self):
        validation_result = self.testing_class.validate(self.test_server_status)
        self.assertTrue(validation_result)

    def test_validation_no_field_time(self):
        test_data = deepcopy(self.test_server_status)
        test_data.pop('time')
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_no_field_start_time(self):
        test_data = deepcopy(self.test_server_status)
        test_data.pop('start_time')
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_no_field_host(self):
        test_data = deepcopy(self.test_server_status)
        test_data.pop('host')
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_wrong_ipv4_in_host(self):
        test_data = deepcopy(self.test_server_status)
        test_data['host']['ipv4'] = 'wron.gi.p.wro'
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_wrong_ipv6_in_host(self):
        test_data = deepcopy(self.test_server_status)
        test_data['host']['ipv6'] = 'wron.gi.p.wro'
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_wrong_udp_port_list_in_host(self):
        test_data = deepcopy(self.test_server_status)
        test_data['host']['udp_port_list'] = ['333344533333', '1']
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_wrong_tcp_port_list_in_host(self):
        test_data = deepcopy(self.test_server_status)
        test_data['host']['tcp_port_list'] = ['333344533333', '1']
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_nsone_wrong_monitor_type(self):
        test_data = deepcopy(self.test_server_status)
        test_data['nsone']['monitor_type'] = "wrong"
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_log_function(self):
        self.testing_class.current_server_state = self.test_server_status
        result = self.testing_class.log(self.test_server_status['host'], 'host')
        db_data = self.log_collection.find_one()
        test_data = deepcopy(self.test_server_status)
        test_data['nsone']['monitor_type'] = "wrong"
        validation_result = self.testing_class.validate(test_data)
        self.assertEqual(self.test_server_status, db_data)
