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

import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import unittest
import os
import datetime
import requests_mock
import responses
from copy import deepcopy
from urlparse import urljoin

import pymongo
from nsone.rest.errors import ResourceException

import mongo_logger

from mock import Mock, patch, mock

import settings
from server_deployment.cds_api import CDSAPI
from server_deployment.infradb import InfraDBAPI
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError

from server_deployment.nsone_class import Ns1Deploy

import server_deployment.server_state as server_state
import server_deployment.abstract_sequence as abs_sequence
import server_deploy as deploy_sequence
import destroying_server as destroy_sequence
from server_deployment.test_utilites import NS1MonitorMock, MockNSONE, Objectview, MockedInfraDB, NS1ZoneMock, \
    MockedServerClass, NS1Record, MockedExecOutput

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
        print("RUN_TEST %s" % self._testMethodName)

    # def tearDown(self):
    #     self.mongo_cli.drop_database('test_database')
    #     # remove all temporary test files
    #     os.system("rm -r %s" % TEST_DIR)

    def check_log_exist(self):
        return self.log_collection.find_one()
        # return self.log_collection.find().sort("_id", -1).limit(1)


class TestLoggerClass(TestAbstract):
    testing_class = mongo_logger.MongoLogger(
        'test_host', datetime.datetime.now().isoformat()
    )

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
        self.assertTrue(validation_result)

    def test_log_function(self):
        self.testing_class.current_server_state = self.test_server_status
        result = self.testing_class.log(self.test_server_status['host'], 'host')
        db_data = self.log_collection.find_one()
        test_data = deepcopy(self.test_server_status)
        test_data['nsone']['monitor_type'] = "wrong"
        validation_result = self.testing_class.validate(test_data)
        # self.assertEqual(self.test_server_status, db_data)


class TestInfraDBAPI(TestAbstract):

    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.infra_db_url = 'http://localhost:8000/api/'
        # settings.INFRADB_URL = self.infra_db_url

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, urljoin(self.infra_db_url, 'hosting/?code=test_host'),
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            rsps.add(responses.GET, urljoin(self.infra_db_url, 'location/?code=test_loc'),
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            self.testing_class = InfraDBAPI(self.logger, 'test_loc', 'test_host')
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_add_server(self):
        infradb_url = urljoin(self.infra_db_url, 'server/')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, infradb_url,
                     body='{}', status=201,
                     content_type='application/json')
            response_dict = self.testing_class.add_server(
                "test_host",
                "111.111.111.111",
                {
                    "type": 1,
                    "proxy_software_version": 1,
                    "kernel_version": 1,
                }
            )
            self.assertEqual(response_dict, None)

    def test_add_server_error(self):
        infradb_url = urljoin(self.infra_db_url, 'server/')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, infradb_url,
                     body='test error', status=403,
                     content_type='application/json')
            test_data = [
                "test_host",
                "111.111.111.111",
                {
                    "type": 1,
                    "proxy_software_version": 1,
                    "kernel_version": 1,
                },
            ]
            self.assertRaises(DeploymentError, self.testing_class.add_server, *test_data)

    def test_get_location(self):
        location_name = "test_loc"
        test_url = urljoin(self.infra_db_url, 'location/?code=%s' % location_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            loc_data = self.testing_class._get_location(location_name)
            self.assertEqual(loc_data, {"id": 1})

    def test_get_location_empty_answer(self):
        location_name = "test_loc"
        test_url = urljoin(self.infra_db_url, 'location/?code=%s' % location_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[]', status=200,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_location, location_name)

    def test_get_location_server_error(self):
        location_name = "test_loc"
        test_url = urljoin(self.infra_db_url, 'location/?code=%s' % location_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_location, location_name)

    def test_get_hosting(self):
        hosting_name = "test_host"
        test_url = urljoin(self.infra_db_url, 'hosting/?code=%s' % hosting_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            loc_data = self.testing_class._get_hosting(hosting_name)
            self.assertEqual(loc_data, {"id": 1})

    def test_get_hosting_empty_answer(self):
        hosting_name = "test_host"
        test_url = urljoin(self.infra_db_url, 'hosting/?code=%s' % hosting_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[]', status=200,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_hosting, hosting_name)

    def test_get_hosting_server_error(self):
        hosting_name = "test_host"
        test_url = urljoin(self.infra_db_url, 'hosting/?code=%s' % hosting_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_hosting, hosting_name)


class TestCDSAPI(TestAbstract):
    @patch("settings.CDS_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.cds_url = 'http://localhost:8000/api/'
        self.server_group_id = 123
        # settings.INFRADB_URL = self.infra_db_url

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        self.host_name = "test_host"
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET,
                     urljoin(settings.CDS_URL, 'v1/server_groups/%s' % self.server_group_id),
                     body='{"groupType":"BP"}', status=200,
                     content_type='application/json')
            rsps.add(responses.GET,
                     urljoin(settings.CDS_URL, 'v1/ssl_jobs/status'),
                     body='{"highest_ssl_cert_job_id":1}', status=200,
                     content_type='application/json')
            rsps.add(responses.GET,
                     urljoin(settings.CDS_URL, 'v1/app_jobs/status'),
                     body='{"highest_app_job_id":1}', status=200,
                     content_type='application/json')
            rsps.add(responses.GET,
                     urljoin(settings.CDS_URL, 'v1/domain_config_jobs/status'),
                     body='{"highest_domain_config_job_id":1}', status=200,
                     content_type='application/json')
            rsps.add(responses.GET,
                     urljoin(settings.CDS_URL, 'v1/purge_jobs/status'),
                     body='{"highest_purge_job_id":1}', status=200,
                     content_type='application/json')
            rsps.add(responses.GET,
                     urljoin(settings.CDS_URL, '/v1/waf_rule_jobs/status'),
                     body='{"highest_waf_rule_job_id":1}', status=200,
                     content_type='application/json')
            self.testing_class = CDSAPI(self.server_group_id, self.host_name, self.logger)
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_get_server_group(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"groupType":"BP"}', status=200,
                     content_type='application/json')
            response_dict = self.testing_class._get_server_group()
            self.assertEqual(response_dict, {"groupType": "BP"})

    def test_get_server_group_error(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_server_group)


    def test_get_server_group_not_found(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='[]', status=200,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_server_group)

    def test_get_server_group_wrong_type(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"groupType":"NotBP"}', status=200,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_server_group)

    def test_get_highest_waf_version(self):
        cds_url = urljoin(self.cds_url, '/v1/waf_rule_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_waf_rule_job_id":200}', status=200,
                     content_type='application/json')
            response = self.testing_class._get_highest_waf_version()
            self.assertEqual(response, 200)

    def test_get_highest_waf_version_error(self):
        cds_url = urljoin(self.cds_url, '/v1/waf_rule_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_highest_waf_version)

    def test_get_highest_ssl_version(self):
        cds_url = urljoin(self.cds_url, 'v1/ssl_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_ssl_cert_job_id":201}', status=200,
                     content_type='application/json')
            response = self.testing_class._get_highest_ssl_version()
            self.assertEqual(response, 201)

    def test_get_highest_ssl_version_error(self):
        cds_url = urljoin(self.cds_url, 'v1/ssl_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_highest_ssl_version)

    def test_get_highest_sdk_version(self):
        cds_url = urljoin(self.cds_url, 'v1/app_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_app_job_id":202}', status=200,
                     content_type='application/json')
            response = self.testing_class._get_highest_sdk_version()
            self.assertEqual(response, 202)

    def test_get_highest_sdk_version_error(self):
        cds_url = urljoin(self.cds_url, 'v1/app_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_highest_sdk_version)

    def test_get_highest_purge_version(self):
        cds_url = urljoin(self.cds_url, 'v1/purge_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_purge_job_id":203}', status=200,
                     content_type='application/json')
            response = self.testing_class._get_highest_purge_version()
            self.assertEqual(response, 203)

    def test_get_highest_purge_version_error(self):
        cds_url = urljoin(self.cds_url, 'v1/purge_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_highest_purge_version)

    def test_get_highest_domain_version(self):
        cds_url = urljoin(self.cds_url, 'v1/domain_config_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            response = self.testing_class._get_highest_domain_version()
            self.assertEqual(response, 205)

    def test_get_highest_domain_version_error(self):
        cds_url = urljoin(self.cds_url, 'v1/domain_config_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class._get_highest_domain_version)

    def test_check_server_exist(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"_id":205}', status=200,
                     content_type='application/json')
            response = self.testing_class.check_server_exist()
            self.assertEqual(response, {"_id":205})

    def test_check_server_exist_error(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class.check_server_exist)

    def test_check_server_exist_server_not_found(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"message":"Server not found"}', status=400,
                     content_type='application/json')
            response = self.testing_class.check_server_exist()
            self.assertEqual(response, False)

    def test_check_server_exist_server_not_found_wrong_message(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"message":"wrongmess"}', status=400,
                     content_type='application/json')
            self.assertRaises(DeploymentError, self.testing_class.check_server_exist)

    def test_add_server(self):
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            self.testing_class.proxy_server = None
            self.testing_class.add_server('111.111.111.111', 'env')
            self.assertEqual(self.testing_class.proxy_server, {"highest_domain_config_job_id":205})

    def test_add_server_wrong_code(self):
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            exception_raised = False
            self.assertRaises(DeploymentError, self.testing_class.add_server, '111.111.111.111', 'env')

    def test_update_server(self):
        proxy_id =1
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers/%s' % proxy_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.PUT, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            self.testing_class.proxy_server = {"_id": proxy_id}
            response = self.testing_class.update_server({'ip': '111.111.111.111', "env": 'env'})
            self.assertEqual(self.testing_class.proxy_server, {"highest_domain_config_job_id":205})

    def test_update_server_wrong_code(self):
        proxy_id = 1
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError, self.testing_class.add_server, '111.111.111.111', 'env'
            )


class TestNS1Class(TestAbstract):

    test_monitor = {
        'status': {'sjc': {'status': 'down', 'since': 1513890023,
                           'fail_set': ['Failure for Rule: output contains this is a test',
                                        'Connection error/Timeout']},
                   'global': {'status': 'up', 'since': 1513890023, 'fail_set': ['sjc']}},
        'notify_list': None, 'notify_repeat': 0, 'notify_failback': True, 'name': 'test-test2.host',
        'mute': False, 'rules': [{'comparison': 'contains', 'key': 'output', 'value': 'this is a test'}],
        'notes': None, 'notify_delay': 0, 'job_type': 'tcp', 'notify_regional': False, 'regions': ['sjc'],
        'active': True, 'v2': True, 'frequency': 60, 'rapid_recheck': False, 'policy': 'quorum',
        'region_scope': 'fixed',
        'config': {'response_timeout': 1000, 'host': 'test-test2.host', 'connect_timeout': 2000,
                     'send': 'GET /test-cache.js HTTP/1.1\nHost: monitor.revsw.net\n\n', 'port': 80},
        'id': '1234',
        "name": 'test-test1.host',
    }

    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        self.mocked_ns1_class = MockNSONE(apikey="1234")
        self.mocked_ns1_monitors = NS1MonitorMock()
        self.host_name = 'test-test1.host'
        self.ip = '111.111.111.111'
        self.testing_class = Ns1Deploy(self.host_name, self.ip, self.logger)
        self.testing_class.ns1 = self.mocked_ns1_class
        self.testing_class.monitor = self.mocked_ns1_monitors
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_get_monitor_list(self):

        monitors = self.testing_class.get_monitor_list()
        # self.assertEquals([self.test_monitor], monitors)

    def test_check_is_monitor_exist(self):
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.list.return_value = [self.test_monitor]
        monitor_exist = self.testing_class.check_is_monitor_exist()
        self.assertEquals(monitor_exist, '1234')

    def test_check_is_monitor_not_exist(self):
        self.testing_class.host_name = "wrong_host_name"
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.list.return_value = [self.test_monitor]
        monitor_exist = self.testing_class.check_is_monitor_exist()
        self.assertFalse(monitor_exist)

    def test_add_monitor(self):
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.create.return_value = {"id": "5432"}
        monitor_id = self.testing_class.add_new_monitor()
        self.assertEquals(monitor_id, '5432')

    def test_add_monitor_fail(self):

        raised_exception = False
        try:
            monitor_id = self.testing_class.add_new_monitor()
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)

    def test_check_get_monitor(self):
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.retrieve.return_value = self.test_monitor
        monitor = self.testing_class.get_monitor('5678')
        self.assertEquals(self.test_monitor, monitor)

    def test_check_get_monitor_fail(self):
        raised_exception = False
        try:
            monitor = self.testing_class.get_monitor('5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)

    def test_check_monitor_status(self):
        status = self.testing_class.check_monitor_status('1234')
        self.assertEquals('up', status)

    def test_delete_monitor(self):
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.delete.return_value = self.test_monitor
        monitor = self.testing_class.delete_monitor('5678')

    def test_delete_monitor_fail(self):
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.delete.side_effect = ResourceException('error')
        with self.assertRaises(DeploymentError):
            self.testing_class.delete_monitor('5678')

    def test_add_feed(self):
        raised_exception = False
        try:
            feed = self.testing_class.add_feed('1234', '5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)


class TestAbstractSequence(TestAbstract):
    @patch("settings.CDS_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.cds_url = 'http://localhost:8000/api/'
        self.server_group_id = 123
        # settings.INFRADB_URL = self.infra_db_url

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        self.host_name = "test-host.test.test"
        args_dict = {
            'first_step': "test_first_step",
            'host_name': self.host_name,
            "IP": '111.111.111.111',
            "number_of_steps_to_execute": None,
            "hosting": None,
            "server_group": '123',
            "dns_balancing_name": "test-dns.test.test",
            "disable_infradb_ssl": True,

        }

        self.args = Objectview(args_dict)
        abs_sequence.InfraDBAPI = MockedInfraDB
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") as ns1_mock:
            ns1_mock.return_value = NS1ZoneMock()
            self.testing_class = abs_sequence.SequenceAbstract(self.args)

        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_get_short_name(self):
        self.testing_class.host_name = "TEST-LOC.HOST.NAME"
        short_name = self.testing_class.get_short_name()
        self.assertEquals(short_name, "TEST-LOC")

    def test_get_short_name_wrong(self):
        self.testing_class.host_name = "TEST-LOC-HOST-NAME"
        exception_raised = False
        try:
            self.testing_class.get_short_name()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)

    def test_get_zone_name(self):
        short_name = self.testing_class.get_zone_name("TEST-LOC.HOST.NAME")
        self.assertEquals(short_name, "HOST.NAME")

    def test_get_zone_name_wrong(self):
        exception_raised = False
        try:
            self.testing_class.get_zone_name("TEST-LOC-HOST-NAME")
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)

    def test_get_location_code(self):
        self.testing_class.host_name = "TEST-LOC.HOST.NAME"
        short_name = self.testing_class.get_location_code()
        self.assertEquals(short_name, "TEST")

    def test_get_location_code_wrong(self):
        self.testing_class.host_name = "TEST.LOC.HOST.NAME"
        exception_raised = False
        try:
            self.testing_class.get_location_code()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)

    def test_run_sequence_wrong_first_step(self):
        self.testing_class.step_sequence = ['another_step',]
        exception_raised = False
        try:
            self.testing_class.run_sequence()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)

class TestDeploymentSequence(TestAbstract):
    @patch("settings.CDS_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(
            settings.MONGO_HOST, settings.MONGO_PORT
        )
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.cds_url = 'http://localhost:8000/api/'
        self.server_group_id = 123
        # settings.INFRADB_URL = self.infra_db_url

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        self.host_name = "test-host.test.test"
        args_dict = {
            'host_name': self.host_name,
            'IP': '111.111.111.11',
            'number_of_steps_to_execute': 1,
            'server_group': 'test',
            'dns_balancing_name': "test-dns.test.test",
            'password': 'password',
            'record_type': "A",
            'hosting': "test_hosting",
            'first_step': "test_first_step",
            "disable_infradb_ssl": True,
            "login": 'test_login',
            "password": 'pass',
        }

        args = Objectview(args_dict)
        abs_sequence.InfraDBAPI = MockedInfraDB
        deploy_sequence.ServerState = MockedServerClass
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") as ns1_mock:
            ns1_mock.return_value = NS1ZoneMock()
            self.testing_class = deploy_sequence.DeploySequence(args)
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_add_to_infradb(self):
        test_class = MockedInfraDB()
        self.testing_class.infradb = test_class
        self.testing_class.add_to_infradb()
        self.assertEquals(
            test_class.called_functions,
            {
                "get_server": [self.host_name, ],
                'add_server': [
                    self.host_name,
                    '111.111.111.11',
                    {
                        "proxy_software_version": 1,
                        "kernel_version": 1,
                        "revsw_module_version": 1,
                    }
                ]
            }
        )

    def test_add_ns1_a_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = None
        self.testing_class.ns1.add_a_record.return_value = {'id':123}

        self.testing_class.add_ns1_a_record()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.add_a_record.assert_called()

    def test_radd_ns1_a_record_wrong_record(self):
        self.testing_class.ns1 = Mock()
        ns1_record = NS1Record()
        ns1_record.data['answers'] = [{"answer": ['222.111.111.11',], "id": "1213"}]
        self.testing_class.ns1.get_a_record.return_value = ns1_record
        exception_raised = False
        try:
            self.testing_class.add_ns1_a_record()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)
        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.add_a_record.assert_not_called()

    def test_radd_ns1_a_record_record_exist(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = NS1Record()
        with self.assertRaises(DeploymentError):
            self.testing_class.add_ns1_a_record()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.add_a_record.assert_not_called()

    @patch("settings.NS1_WAITING_TIME", 0)
    def test_add_ns1_monitor(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = None
        self.testing_class.ns1.add_new_monitor.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'up'
        self.testing_class.ns1.find_feed.return_value = None
        self.testing_class.ns1.add_feed.return_value = 1123

        self.testing_class.add_ns1_monitor()

        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.add_new_monitor.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_called()
        self.testing_class.ns1.add_feed.assert_called()

    @patch("settings.NS1_WAITING_TIME", 0)
    def test_add_ns1_monitor_server_exist(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'up'
        self.testing_class.ns1.find_feed.return_value = None
        self.testing_class.ns1.add_feed.return_value = 1123

        self.testing_class.add_ns1_monitor()

        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.add_new_monitor.assert_not_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_called()
        self.testing_class.ns1.add_feed.assert_called()

    @patch("settings.NS1_WAITING_TIME", 0)
    def test_add_ns1_monitor_not_up(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = None
        self.testing_class.ns1.add_new_monitor.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'down'
        self.testing_class.ns1.find_feed.return_value = None
        self.testing_class.ns1.add_feed.return_value = 1123
        exception_raised = False
        try:
            self.testing_class.add_ns1_monitor()
        except DeploymentError:
            exception_raised = True

        self.assertTrue(exception_raised)
        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.add_new_monitor.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_not_called()
        self.testing_class.ns1.add_feed.assert_not_called()

    @patch("settings.NS1_WAITING_TIME", 0)
    def test_add_ns1_monitor_feed_exist(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = None
        self.testing_class.ns1.add_new_monitor.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'up'
        self.testing_class.ns1.find_feed.return_value = 1123

        self.testing_class.add_ns1_monitor()

        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.add_new_monitor.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_called()
        self.testing_class.ns1.add_feed.assert_not_called()

    def test_add_ns1_balancing_rule(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'up'
        self.testing_class.ns1.find_feed.return_value = 123
        self.testing_class.ns1.add_answer.return_value = 1123

        self.testing_class.add_ns1_balancing_rule()

        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_called()
        self.testing_class.ns1.add_answer.assert_called()

    def test_add_ns1_balancing_rule_monitor_not_exist(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = None
        self.testing_class.ns1.check_monitor_status.return_value = 'up'
        self.testing_class.ns1.find_feed.return_value = 123
        self.testing_class.ns1.add_answer.return_value = 1123
        exception_raised = False
        try:
            self.testing_class.add_ns1_balancing_rule()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)
        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_not_called()
        self.testing_class.ns1.find_feed.assert_not_called()
        self.testing_class.ns1.add_answer.assert_not_called()

    def test_add_ns1_balancing_rule_monitor_not_up(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'down'
        self.testing_class.ns1.find_feed.return_value = 123
        self.testing_class.ns1.add_answer.return_value = 1123
        exception_raised = False
        try:
            self.testing_class.add_ns1_balancing_rule()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)
        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_not_called()
        self.testing_class.ns1.add_answer.assert_not_called()

    def test_add_ns1_balancing_rule_feed_not_found(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = 123
        self.testing_class.ns1.check_monitor_status.return_value = 'up'
        self.testing_class.ns1.find_feed.return_value = None
        self.testing_class.ns1.add_answer.return_value = 1123
        exception_raised = False
        try:
            self.testing_class.add_ns1_balancing_rule()
        except DeploymentError:
            exception_raised = True
        self.assertTrue(exception_raised)
        self.testing_class.ns1.check_is_monitor_exist.assert_called()
        self.testing_class.ns1.check_monitor_status.assert_called()
        self.testing_class.ns1.find_feed.assert_called()
        self.testing_class.ns1.add_answer.assert_not_called()

class TestDestroySequence(TestAbstract):
    @patch("settings.CDS_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(
            settings.MONGO_HOST, settings.MONGO_PORT
        )
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.cds_url = 'http://localhost:8000/api/'
        self.server_group_id = 123
        # settings.INFRADB_URL = self.infra_db_url

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        self.host_name = "test-host.test.test"
        args_dict = {
            'host_name': self.host_name,
            'IP': '111.111.111.11',
            'number_of_steps_to_execute': 1,
            'server_group': 'test',
            'dns_balancing_name': "test-dns.test.test",
            'password': 'password',
            'record_type': "A",
            'hosting': "test_hosting",
            'first_step': "test_first_step",
            "disable_infradb_ssl": True,
            "login": 'test_login',
            "password": 'pass',
        }

        args = Objectview(args_dict)
        abs_sequence.InfraDBAPI = MockedInfraDB
        destroy_sequence.ServerState = MockedServerClass
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") as ns1_mock:
            ns1_mock.return_value = NS1ZoneMock()
            self.testing_class = destroy_sequence.DestroySequence(args)
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_remove_from_infradb(self):
        test_class = MockedInfraDB()
        self.testing_class.infradb = test_class
        self.testing_class.remove_from_infradb()
        # self.assertEquals(
        #     test_class.called_functions,
        #     {
        #         "delete_server": [self.host_name, ],
        #     }
        # )

    def test_remove_ns1_monitor(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = 1

        self.testing_class.remove_ns1_monitor()

        self.testing_class.ns1.check_is_monitor_exist.assert_called_once_with()
        self.testing_class.ns1.delete_feed.assert_called_once_with(settings.NS1_DATA_SOURCE_ID, 1)
        self.testing_class.ns1.delete_monitor.assert_called_once_with(1)

    def test_remove_ns1_monitor_wrong_monitor(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.check_is_monitor_exist.return_value = False

        self.testing_class.remove_ns1_monitor()

        self.testing_class.ns1.check_is_monitor_exist.assert_called_once_with()
        self.testing_class.ns1.delete_feed.assert_not_called()
        self.testing_class.ns1.delete_monitor.assert_not_called()

    def test_remove_ns1_a_record_wrong_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = None

        self.testing_class.remove_ns1_a_record()

        self.testing_class.ns1.get_a_record.assert_called()

    def test_remove_ns1_a_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = NS1Record()

        self.testing_class.remove_ns1_a_record()

        self.testing_class.ns1.get_a_record.assert_called_once()

    @patch("settings.NS1_AFTER_ANSWER_DELETING_WAIT_TIME", 0)
    def test_remove_ns1_balancing_rule(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = NS1Record()
        self.testing_class.ns1.check_record_answers.return_value = 31

        self.testing_class.remove_ns1_balancing_rule()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.check_record_answers.assert_not_called()

    @patch("settings.NS1_AFTER_ANSWER_DELETING_WAIT_TIME", 0)
    def test_remove_ns1_balancing_rule_wrong_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = None
        self.testing_class.ns1.check_record_answers.return_value = 31

        self.testing_class.remove_ns1_balancing_rule()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.check_record_answers.assert_not_called()

    @patch("settings.NS1_AFTER_ANSWER_DELETING_WAIT_TIME", 0)
    def test_remove_ns1_balancing_rule_low_answers(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = NS1Record()
        self.testing_class.ns1.check_record_answers.return_value = 20

        self.testing_class.remove_ns1_balancing_rule()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.check_record_answers.assert_not_called()

    @patch("settings.NS1_AFTER_ANSWER_DELETING_WAIT_TIME", 0)
    def test_remove_ns1_balancing_rule_ip_not_found(self):
        self.testing_class.ns1 = Mock()
        ns1_record = NS1Record()
        ns1_record.data['answers'] = [{"answer": ['222.111.111.11',], "id": "1213"}]
        self.testing_class.ns1.get_a_record.return_value = ns1_record
        self.testing_class.ns1.check_record_answers.return_value = 31

        self.testing_class.remove_ns1_balancing_rule()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.check_record_answers.assert_not_called()


class TestServerState(TestAbstract):
    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat()
        )
        self.mocked_ns1_class = MockNSONE(apikey="1234")
        self.mocked_ns1_monitors = NS1MonitorMock()
        self.host_name = 'test-test1.host'
        self.ip = '111.111.111.111'
        self.connection = Mock()
        server_state.paramiko = Mock()
        # with patch("server_deployment.server_state.paramiko") as self.paramiko:

            # self.paramiko.SSHClient = Mock()
        server_state.paramiko.SSHClient.connect.return_value = self.connection
        server_state.paramiko.RSAKey.from_private_key_file.return_value = 'key'
        self.testing_class = ServerState(self.host_name, 'login', 'password', self.logger)

        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_check_hostname(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test_hostname.test.test',]),'3'
        ]
        ret_data = self.testing_class.check_hostname()
        self.assertEquals(ret_data, 'test_hostname.test.test')
        self.testing_class.client.exec_command.assert_called_with("hostname")

    def test_check_install_package(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'Package: test_package',
                'Status: install ok installed\n',
            ]),'3'
        ]
        ret_data = self.testing_class.check_install_package('test_package')
        self.assertTrue(ret_data)
        self.testing_class.client.exec_command.assert_called_with("dpkg -s test_package")

    def test_check_install_package_not_installed(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['ok','not installed\n',]),'3'
        ]
        ret_data = self.testing_class.check_install_package('test_package')
        self.assertFalse(ret_data)
        self.testing_class.client.exec_command.assert_called_with("dpkg -s test_package")

    def test_check_system_version(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'DISTRIB_RELEASE=14.04',
            ]),'3'
        ]
        ret_data = self.testing_class.check_system_version()
        self.assertEqual(ret_data, '14.04')
        self.testing_class.client.exec_command.assert_called_with(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )

    def test_check_system_version_not14_04(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'DISTRIB_RELEASE=16.05',
            ]),'3'
        ]
        ret_data = self.testing_class.check_system_version()
        self.assertEqual(ret_data, '16.05')
        self.testing_class.client.exec_command.assert_called_with(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )

    def test_check_system_version_wrong_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ]),'3'
        ]
        ret_data = self.testing_class.check_system_version()
        self.assertEqual(ret_data, '14.04')
        self.testing_class.client.exec_command.assert_called_with(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )

    def test_execute_command_with_log(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ]),'3'
        ]
        ret_data = self.testing_class.execute_command_with_log('command')
        self.assertEqual(ret_data, 0)
        self.testing_class.client.exec_command.assert_called_with(
            'command'
        )

    def test_execute_command_with_log_wrong_status(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ], return_status=1),'3'
        ]
        self.assertRaises(
            DeploymentError, self.testing_class.execute_command_with_log, 'command'
        )
        self.testing_class.client.exec_command.assert_called_with(
            'command'
        )

    def test_execute_command_with_log_wrong_status_without_check(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ], return_status=1),'3'
        ]
        ret_data = self.testing_class.execute_command_with_log('command', check_status=False)
        self.assertEqual(ret_data, 1)
        self.testing_class.client.exec_command.assert_called_with(
            'command'
        )

    def test_check_ram_size(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'MemTotal: %s kB' % (30*1024*1024),
            ]), '3'
        ]
        ret_data = self.testing_class.check_ram_size()
        self.testing_class.client.exec_command.assert_called_with(
            "grep 'MemTotal:'  /proc/meminfo"
        )

    def test_check_ram_size_not_enouph(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'MemTotal: %s kB' % (30*1024),
            ]), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_ram_size
        )
        self.testing_class.client.exec_command.assert_called_with(
            "grep 'MemTotal:'  /proc/meminfo"
        )

    def test_check_hw_architecture(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'x86_64',
            ]), '3'
        ]
        ret_data = self.testing_class.check_hw_architecture()
        self.testing_class.client.exec_command.assert_called_with(
            "arch"
        )

    def test_check_hw_architecture_wrong_arch(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrog arch',
            ]), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_hw_architecture
        )
        self.testing_class.client.exec_command.assert_called_with(
            "arch"
        )

    def test_check_os_version(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'DISTRIB_RELEASE=14.04',
            ]), '3'
        ]
        ret_data = self.testing_class.check_os_version()
        self.testing_class.client.exec_command.assert_called_with(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )

    def test_check_os_version_wrong_os_version(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'DISTRIB_RELEASE=16.06',
            ]), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_os_version
        )
        self.testing_class.client.exec_command.assert_called_with(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )

    def test_check_os_version_wrong_resp(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong',
            ]), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_os_version
        )
        self.testing_class.client.exec_command.assert_called_with(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )

    def test_check_ping_8888(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                '1000 packets transmitted, 1000 received, 0% packet loss, time 13347ms',
            ]), '3'
        ]
        ret_data = self.testing_class.check_ping_8888()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo ping -f -c 1000 8.8.8.8"
        )

    def test_check_ping_8888_packet_loss(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                '1000 packets transmitted, 1000 received, 1% packet loss, time 13347ms',
            ]), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_ping_8888
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo ping -f -c 1000 8.8.8.8"
        )

    def test_check_free_space(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'Filesystem     1K-blocks     Used Available Use% Mounted on',
                'udev             1848560        0   1848560   0% /dev',
                '/dev/sda5      181354808 17830480 154288976  11% /',
            ]), '3'
        ]
        ret_data = self.testing_class.check_free_space()
        self.testing_class.client.exec_command.assert_called_with(
            "df"
        )

    def testcheck_free_space_not_enouph(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'Filesystem     1K-blocks     Used Available Use% Mounted on',
                'udev             1848560        0   1848560   0% /dev',
                '/dev/sda5      181354808 17830480 1006  11% /',
            ]), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_free_space
        )
        self.testing_class.client.exec_command.assert_called_with(
            "df"
        )

    def test_run_puppet(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
            ]), '3'
        ]
        ret_data = self.testing_class.run_puppet()
        self.assertEquals(ret_data, 0)
        self.testing_class.client.exec_command.assert_called_with(
            "sudo puppet agent -t --server=TESTSJC20-INSTALL01.REVSW.NET"
        )

    def test_run_puppet_wrong_status_install_ok(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'Exiting; no certificate found and waitforcert is disabled',
            ], return_status=1), '3'
        ]
        ret_data = self.testing_class.run_puppet()
        self.assertEquals(ret_data, 0)
        self.testing_class.client.exec_command.assert_called_with(
            "sudo puppet agent -t --server=TESTSJC20-INSTALL01.REVSW.NET"
        )

    def test_run_puppet_wrong_status_install_not_ok(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong',
            ], return_status=1), '3'
        ]
        ret_data = self.testing_class.run_puppet()
        self.assertEquals(ret_data, 1)
        self.testing_class.client.exec_command.assert_called_with(
            "sudo puppet agent -t --server=TESTSJC20-INSTALL01.REVSW.NET"
        )

    def test_remove_puppet(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test']), '3'
        ]
        ret_data = self.testing_class.remove_puppet()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo rm -r /var/lib/puppet/ssl"
        )

    def test_remove_puppet_wrong_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test'], return_status=1), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.remove_puppet
        )

    def test_configure_puppet(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test']), '3'
        ]
        ret_data = self.testing_class.configure_puppet()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo puppet agent -t --server=TESTSJC20-INSTALL01.REVSW.NET"
        )

    def test_configure_puppet_wrong_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test'], return_status=1), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.configure_puppet
        )

if __name__ == '__main__':
    unittest.main()
