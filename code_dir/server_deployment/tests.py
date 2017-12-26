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
from server_deployment.utilites import DeploymentError

from server_deployment.nsone_class import Ns1Deploy

from code_dir.server_deployment.test_utilites import NS1MonitorMock, MockNSONE

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

    def tearDown(self):
        self.mongo_cli.drop_database('test_database')
        # remove all temporary test files
        os.system("rm -r %s" % TEST_DIR)

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
        self.assertFalse(validation_result)

    def test_log_function(self):
        self.testing_class.current_server_state = self.test_server_status
        result = self.testing_class.log(self.test_server_status['host'], 'host')
        db_data = self.log_collection.find_one()
        test_data = deepcopy(self.test_server_status)
        test_data['nsone']['monitor_type'] = "wrong"
        validation_result = self.testing_class.validate(test_data)
        self.assertEqual(self.test_server_status, db_data)


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
        self.testing_class = InfraDBAPI(self.logger)
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_add_server(self):
        infradb_url = urljoin(self.infra_db_url, 'server/')
        self.testing_class._get_location = Mock(return_value={"id": 1})
        self.testing_class._get_hosting = Mock(return_value={"id": 1})
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
                },
                "test_loc",
                "test_host"
            )
            self.assertEqual(response_dict, None)
            log = self.check_log_exist()
            self.assertEquals(
                log['infraDB'],
                {
                    "fw": "no",
                    "server_add": "yes"
                }
            )

    def test_add_server_error(self):
        infradb_url = urljoin(self.infra_db_url, 'server/')
        self.testing_class._get_location = Mock(return_value={"id": 1})
        self.testing_class._get_hosting = Mock(return_value={"id": 1})
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
                "test_loc",
                "test_host"
            ]
            try:
                self.assertRaises(DeploymentError, self.testing_class.add_server, *test_data)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['infraDB'],
                {
                    "fw": "no",
                    "server_add": "fail",
                    "log": "Server error. Status: 403 Error: test error"
                }
            )

    def test_get_location(self):
        location_name = "test_loc"
        test_url = urljoin(self.infra_db_url, 'location?code=%s' % location_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            loc_data = self.testing_class._get_location(location_name)
            self.assertEqual(loc_data, {"id": 1})

    def test_get_location_empty_answer(self):
        location_name = "test_loc"
        test_url = urljoin(self.infra_db_url, 'location?code=%s' % location_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[]', status=200,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_location, location_name)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['infraDB'],
                {
                    "fw": "no",
                    "server_add": "fail",
                    "log": "Server error. Wrong location code. Location not found"
                }
            )

    def test_get_location_server_error(self):
        location_name = "test_loc"
        test_url = urljoin(self.infra_db_url, 'location?code=%s' % location_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='test error', status=403,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_location, location_name)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['infraDB'],
                {
                    "fw": "no",
                    "server_add": "fail",
                    "log": "Server error. Status: 403 Error: test error"
                }
            )

    def test_get_hosting(self):
        hosting_name = "test_host"
        test_url = urljoin(self.infra_db_url, 'hosting?name=%s' % hosting_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            loc_data = self.testing_class._get_hosting(hosting_name)
            self.assertEqual(loc_data, {"id": 1})

    def test_get_hosting_empty_answer(self):
        hosting_name = "test_host"
        test_url = urljoin(self.infra_db_url, 'hosting?name=%s' % hosting_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[]', status=200,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_hosting, hosting_name)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['infraDB'],
                {
                    "fw": "no",
                    "server_add": "fail",
                    "log": "Server error. Wrong hosting provider name. Hosting provider not found"
                }
            )

    def test_get_hosting_server_error(self):
        hosting_name = "test_host"
        test_url = urljoin(self.infra_db_url, 'hosting?name=%s' % hosting_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='test error', status=403,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_hosting, hosting_name)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['infraDB'],
                {
                    "fw": "no",
                    "server_add": "fail",
                    "log": "Server error. Status: 403 Error: test error"
                }
            )


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
        self.testing_class = CDSAPI(self.server_group_id, self.host_name, self.logger)
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_get_server_group(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"cds_url":"BP"}', status=200,
                     content_type='application/json')
            response_dict = self.testing_class._get_server_group()
            self.assertEqual(response_dict, {"cds_url":"BP"})
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "yes"},
            )

    def test_get_server_group_error(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_server_group)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

    def test_get_server_group_not_found(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='', status=200,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_server_group)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Wrong server group name. Server group not found"},
            )

    def test_get_server_group_wrong_type(self):
        cds_url = urljoin(self.cds_url, 'v1/server_groups/%s' % self.server_group_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"cds_url":"BP"}', status=200,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_server_group)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "CDS  error. Wrong server group"},
            )

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
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_highest_waf_version)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

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
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_highest_ssl_version)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

    def test_get_highest_sdk_version(self):
        cds_url = urljoin(self.cds_url, 'v1/app_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_ssl_cert_job_id":202}', status=200,
                     content_type='application/json')
            response = self.testing_class._get_highest_sdk_version()
            self.assertEqual(response, 202)

    def test_get_highest_sdk_version_error(self):
        cds_url = urljoin(self.cds_url, 'v1/app_jobs/status')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_highest_sdk_version)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

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
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_highest_purge_version)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

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
            try:
                self.assertRaises(DeploymentError, self.testing_class._get_highest_domain_version)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

    def test_check_server_exist(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            response = self.testing_class.check_server_exist()
            self.assertEqual(response, {"highest_domain_config_job_id":205})

    def test_check_server_exist_error(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class.check_server_exist)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 403 Error: test error"},
            )

    def test_check_server_exist_server_not_found(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='Server not found', status=400,
                     content_type='application/json')
            response = self.testing_class.check_server_exist()
            self.assertEqual(response, False)

    def test_check_server_exist_server_not_found_wrong_message(self):
        cds_url = urljoin(self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class.check_server_exist)
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 400 Error: wrongmess"},
            )

    def test_add_server(self):
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            response = self.testing_class.add_server('111.111.111.111', 'env')
            self.assertEqual(response, {"highest_domain_config_job_id":205})
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_add": "fail", "log": "Server error. Status: 400 Error: wrongmess"},
            )

    def test_add_server_wrong_code(self):
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            try:
                self.assertRaises(DeploymentError, self.testing_class.add_server, '111.111.111.111', 'env')
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_add": "fail", "log": "Server error. Status: 400 Error: wrongmess"},
            )

    def test_update_server(self):
        proxy_id =1
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers/%s' % proxy_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.PUT, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            response = self.testing_class.update_server({'ip': '111.111.111.111', "env": 'env'})
            self.assertEqual(response, {"highest_domain_config_job_id":205})

    def test_update_server_wrong_code(self):
        proxy_id = 1
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers/%s' % proxy_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.PUT, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            try:
                self.assertRaises(
                    DeploymentError, self.testing_class.add_server, {'ip': '111.111.111.111', "env": 'env'}
                )
            except Exception:
                pass
            log = self.check_log_exist()
            self.assertEquals(
                log['CDS'],
                {"sever_group": "fail", "log": "Server error. Status: 400 Error: wrongmess"},
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
        'id': '1234'
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
        self.assertEquals([self.test_monitor], monitors)

    def test_check_is_monitor_exist(self):
        self.mocked_ns1_monitors.monitor_list.append(self.test_monitor)

        monitor_exist = self.testing_class.check_monitor_exist()
        self.assertEquals(monitor_exist, '5678')

    def test_check_is_monitor_not_exist(self):
        monitor_exist = self.testing_class.check_monitor_exist()
        self.assertFalse(monitor_exist)

    def test_add_monitor(self):
        monitor_id = ''
        raised_exception = False
        try:
            monitor_id = self.testing_class.add_new_monitor()
        except DeploymentError as e:
            raised_exception = True
        self.assertFalse(raised_exception)
        self.assertEquals(monitor_id, '5432')

    def test_add_monitor_fail(self):

        raised_exception = False
        try:
            monitor_id = self.testing_class.add_new_monitor()
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)

    def test_check_get_monitor(self):
        monitor =None
        self.mocked_ns1_monitors.monitor_list.append(self.test_monitor)
        raised_exception = False
        try:
            monitor = self.testing_class.get_monitor('5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertFalse(raised_exception)
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
        raised_exception = False
        try:
            monitor = self.testing_class.delete_monitor('5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertFalse(raised_exception)

    def test_delete_monitor_fail(self):
        raised_exception = False
        try:
            monitor = self.testing_class.delete_monitor('5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)

    def test_add_feed(self):
        raised_exception = False
        try:
            feed = self.testing_class.add_feed('1234', '5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)


if __name__ == '__main__':
    unittest.main()