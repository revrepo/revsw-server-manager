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

import nsone
from nsone.zones import ZoneException

sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import unittest
import os
import datetime
import responses
from copy import deepcopy
from urlparse import urljoin
import check_server_status
import pymongo
from nsone.rest.errors import ResourceException

import mongo_logger

from mock import Mock, patch, mock

import settings
from server_deployment.cds_api import CDSAPI
from server_deployment.infradb import InfraDBAPI
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError, MongoDBHandler
from server_deployment.nsone_class import Ns1Deploy
from server_deployment.test_utilites import NS1MonitorMock, MockNSONE, Objectview, \
    MockedInfraDB, NS1ZoneMock, MockedArgPars,\
    MockedServerClass, NS1Record, MockedExecOutput, MockedNagiosClass, NS1MockedRecord

import server_deployment.server_state as server_state
import server_deployment.abstract_sequence as abs_sequence
import server_deploy as deploy_sequence
import destroying_server as destroy_sequence
import check_server_status as check_sequence
import server_deployment.nagios_class as nagios_deploy
import server_deployment.cds_api as cds_deploy
import server_deployment.nsone_class as ns1
import server_deployment.cacti as cacti_deploy


TEST_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "temporary_testing_files/"
)


class TestAbstract(unittest.TestCase):
    testing_class = None
    logger_steps = [
        "check_server_consistency",
    ]
    current_server_state = {
        "time": None,
        "check_server_consistency": {
            "runned": "no",
        },
    }
    logger_schema = {
        "type": "object",
        "properties": {
            "time": {"type": "string"},
            "start_time": {"type": "string"},
            "initial_data": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string"},
                    "ip": {
                        "type": "string",
                        "pattern": "(([0-9]|[1-9][0-9]|1[0-9]"
                                   "{2}|2[0-4][0-9]|25[0-5])\.)"
                                   "{3}([0-9]|[1-9][0-9]|1[0-9]"
                                   "{2}|2[0-4][0-9]|25[0-5])"
                    },
                    "login": {"type": "string"},
                    "password": {"type": "string"},

                }
            },
            "check_server_consistency": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "check_ram_size": {"type": "string", "pattern": "yes|no|fail"},
                    "check_free_space": {"type": "string", "pattern": "yes|no|fail"},
                    "check_hw_architecture": {"type": "string", "pattern": "yes|no|fail"},
                    "check_os_version": {"type": "string", "pattern": "yes|no|fail"},
                    "check_ping_8888": {"type": "string", "pattern": "yes|no|fail"},
                    "hostname": {"type": "string"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
        },
        "required": [
            "time",
            "start_time",
            "initial_data",
            "check_server_consistency",

        ]
    }

    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        settings.MONGO_DB_NAME = 'test_database'
        settings.MONGO_HOST = 'localhost'
        settings.MONGO_PORT = 27017
        self.mongo_cli = pymongo.MongoClient(
            settings.MONGO_HOST, settings.MONGO_PORT
        )
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    # def tearDown(self):

        # self.mongo_cli.drop_database('test_database')
        # remove all temporary test files
        # os.system("rm -r %s" % TEST_DIR)

    def check_log_exist(self):
        return self.log_collection.find_one()
        # return self.log_collection.find().sort("_id", -1).limit(1)


class TestLoggerClass(TestAbstract):
    logger_steps = [
        "check_server_consistency",
    ]
    current_server_state = {
        "time": None,
        "check_server_consistency": {
            "runned": "no",
        },
    }
    logger_schema = {
        "type": "object",
        "properties": {
            "time": {"type": "string"},
            "start_time": {"type": "string"},
            "initial_data": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string"},
                    "ip": {
                        "type": "string",
                        "pattern": "(([0-9]|[1-9][0-9]|1[0-9]"
                                   "{2}|2[0-4][0-9]|25[0-5])\.)"
                                   "{3}([0-9]|[1-9][0-9]|1[0-9]"
                                   "{2}|2[0-4][0-9]|25[0-5])"
                    },
                    "login": {"type": "string"},
                    "password": {"type": "string"},

                }
            },
            "check_server_consistency": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "check_ram_size": {"type": "string", "pattern": "yes|no|fail"},
                    "check_free_space": {"type": "string", "pattern": "yes|no|fail"},
                    "check_hw_architecture": {"type": "string", "pattern": "yes|no|fail"},
                    "check_os_version": {"type": "string", "pattern": "yes|no|fail"},
                    "check_ping_8888": {"type": "string", "pattern": "yes|no|fail"},
                    "hostname": {"type": "string"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
        },
        "required": [
            "time",
            "start_time",
            "initial_data",
            "check_server_consistency",

        ]
    }
    testing_class = mongo_logger.MongoLogger(
        'test_host', datetime.datetime.now().isoformat(),
        {
            "hostname": 'hostname',
            "ip": '111.111.111.111',
            "login": 'login',
            "password": 'passw',
        },
        logger_schema,
        current_server_state,
        logger_steps

    )

    test_server_status = {
        "time": datetime.datetime.now().isoformat(),
        "start_time": datetime.datetime.now().isoformat(),
        "initial_data": {
            "hostname": 'test_host',
            "ip": '127.0.0.1',
            "login": "test_login",
            "password": "test_password",
        },
        "check_server_consistency": {
            "runned": "no",
        },
        "check_hostname": {
            "runned": "no",
        },
        "add_ns1_a_record": {
            "runned": "no",
        },
        "add_to_infradb": {
            "runned": "no",
        },
        "update_fw_rules": {
            "runned": "no",
        },
        "install_puppet": {
            "runned": "no",
        },
        "run_puppet": {
            "runned": "no",
        },
        "add_to_cds": {
            "runned": "no",
        },
        "add_to_nagios": {
            "runned": "no",
        },
        "add_ns1_monitor": {
            "runned": "no",
        },
        "add_ns1_balancing_rule": {
            "runned": "no",
        },
        "add_to_pssh_file": {
            "runned": "no",
        },
    }

    def test_validation(self):
        validation_result = self.testing_class.validate(
            self.test_server_status
        )
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
        test_data.pop('initial_data')
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    def test_validation_wrong_ipv4_in_host(self):
        test_data = deepcopy(self.test_server_status)
        test_data['initial_data']['ip'] = 'wron.gi.p.wro'
        validation_result = self.testing_class.validate(test_data)
        self.assertFalse(validation_result)

    # def test_log_function(self):
    #     self.testing_class.current_server_state = self.test_server_status
    #     self.testing_class.log({"runned": "yes"}, 'check_server_consistency')
    #     self.log_collection.find_one()
    #     test_data = deepcopy(self.test_server_status)
    #     test_data['nsone']['monitor_type'] = "wrong"
    #     validation_result = self.testing_class.validate(test_data)
    #     # self.assertEqual(self.test_server_status, db_data)


class TestInfraDBAPI(TestAbstract):

    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
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

        self.infra_db_url = 'http://localhost:8000/api/'
        # settings.INFRADB_URL = self.infra_db_url

        self.logger = Mock()
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin(self.infra_db_url, 'hosting/?code=test_host'),
                body='[{"id":1}]', status=200,
                content_type='application/json'
            )
            rsps.add(
                responses.GET,
                urljoin(self.infra_db_url, 'location/?code=test_loc'),
                body='[{"id":1}]',
                status=200,
                content_type='application/json'
            )
            self.testing_class = InfraDBAPI(
                self.logger, 'test_loc', 'test_host'
            )
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
            self.assertRaises(
                DeploymentError,
                self.testing_class.add_server,
                *test_data
            )

    def test_get_location(self):
        location_name = "test_loc"
        test_url = urljoin(
            self.infra_db_url, 'location/?code=%s' % location_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            loc_data = self.testing_class._get_location(location_name)
            self.assertEqual(loc_data, {"id": 1})

    def test_get_location_empty_answer(self):
        location_name = "test_loc"
        test_url = urljoin(
            self.infra_db_url, 'location/?code=%s' % location_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[]', status=200,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_location,
                location_name
            )

    def test_get_location_server_error(self):
        location_name = "test_loc"
        test_url = urljoin(
            self.infra_db_url,
            'location/?code=%s' % location_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_location,
                location_name
            )

    def test_get_hosting(self):
        hosting_name = "test_host"
        test_url = urljoin(
            self.infra_db_url, 'hosting/?code=%s' % hosting_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[{"id":1}]', status=200,
                     content_type='application/json'
                     )
            loc_data = self.testing_class._get_hosting(hosting_name)
            self.assertEqual(loc_data, {"id": 1})

    def test_get_hosting_empty_answer(self):
        hosting_name = "test_host"
        test_url = urljoin(
            self.infra_db_url, 'hosting/?code=%s' % hosting_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='[]', status=200,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_hosting,
                hosting_name
            )

    def test_get_hosting_server_error(self):
        hosting_name = "test_host"
        test_url = urljoin(
            self.infra_db_url, 'hosting/?code=%s' % hosting_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, test_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_hosting,
                hosting_name
            )


class TestCDSAPI(TestAbstract):
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

        self.logger = Mock()
        # adding MongoDb logger to logger handler
        for handler in cds_deploy.logger.handlers:
            if isinstance(handler, MongoDBHandler):
                handler.add_mongo_logger(self.logger)
        self.host_name = "test_host"
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET,
                     urljoin(
                         settings.CDS_URL,
                         'v1/server_groups/%s' % self.server_group_id
                     ),
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
            self.testing_class = CDSAPI(
                self.server_group_id, self.host_name, self.logger
            )
        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_get_server_group(self):
        cds_url = urljoin(
            self.cds_url, 'v1/server_groups/%s' % self.server_group_id
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"groupType":"BP"}', status=200,
                     content_type='application/json')
            response_dict = self.testing_class._get_server_group()
            self.assertEqual(response_dict, {"groupType": "BP"})

    def test_get_server_group_error(self):
        cds_url = urljoin(
            self.cds_url, 'v1/server_groups/%s' % self.server_group_id
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError, self.testing_class._get_server_group
            )

    def test_get_server_group_not_found(self):
        cds_url = urljoin(
            self.cds_url, 'v1/server_groups/%s' % self.server_group_id
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='[]', status=200,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError, self.testing_class._get_server_group
            )

    def test_get_server_group_wrong_type(self):
        cds_url = urljoin(
            self.cds_url, 'v1/server_groups/%s' % self.server_group_id
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"groupType":"NotBP"}', status=200,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError, self.testing_class._get_server_group
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
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_highest_waf_version
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
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_highest_ssl_version
            )

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
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_highest_sdk_version
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
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_highest_purge_version
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
            self.assertRaises(
                DeploymentError,
                self.testing_class._get_highest_domain_version
            )

    def test_check_server_exist(self):
        cds_url = urljoin(
            self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"_id":205}', status=200,
                     content_type='application/json')
            response = self.testing_class.check_server_exist()
            self.assertEqual(response, {"_id": 205})

    def test_check_server_exist_error(self):
        cds_url = urljoin(
            self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='test error', status=403,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError, self.testing_class.check_server_exist
            )

    def test_check_server_exist_server_not_found(self):
        cds_url = urljoin(
            self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"message":"Server not found"}', status=400,
                     content_type='application/json')
            response = self.testing_class.check_server_exist()
            self.assertEqual(response, False)

    def test_check_server_exist_server_not_found_wrong_message(self):
        cds_url = urljoin(
            self.cds_url, 'v1/proxy_servers/byname/%s' % self.host_name
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, cds_url,
                     body='{"message":"wrongmess"}', status=400,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError, self.testing_class.check_server_exist
            )

    def test_add_server(self):
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            self.testing_class.proxy_server = None
            self.testing_class.add_server('111.111.111.111', 'env')
            self.assertEqual(
                self.testing_class.proxy_server,
                {"highest_domain_config_job_id": 205}
            )

    def test_add_server_wrong_code(self):
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError,
                self.testing_class.add_server,
                '111.111.111.111',
                'env'
            )

    def test_update_server(self):
        proxy_id = 1
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers/%s' % proxy_id)
        with responses.RequestsMock() as rsps:
            rsps.add(responses.PUT, cds_url,
                     body='{"highest_domain_config_job_id":205}', status=200,
                     content_type='application/json')
            self.testing_class.proxy_server = {"_id": proxy_id}
            self.testing_class.update_server(
                {'ip': '111.111.111.111', "env": 'env'}
            )
            self.assertEqual(
                self.testing_class.proxy_server,
                {"highest_domain_config_job_id": 205}
            )

    def test_update_server_wrong_code(self):
        proxy_id = 1
        cds_url = urljoin(self.cds_url, '/v1/proxy_servers')
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST, cds_url,
                     body='wrongmess', status=400,
                     content_type='application/json')
            self.assertRaises(
                DeploymentError,
                self.testing_class.add_server,
                '111.111.111.111',
                'env'
            )

    def test_check_need_update_versions(self):
        self.testing_class.highest_versions = {
            'ssl': 100,
            'sdk': 100,
            'waf': 100,
            'domain': 100,
            'purge': 100,
        }
        self.testing_class.proxy_server = {
            "ssl_cert_version": 100,
            "app_config_version": 100,
            "domain_config_version": 100,
            "waf_rule_version": 100,
            "purge_version": 100

        }
        check_list = self.testing_class.check_need_update_versions()

        self.assertEquals(
            check_list,
            {
                'ssl': False,
                'waf_sdk': False,
                'domain_purge': False
            }
        )

    def test_check_need_update_versions_low_ssl(self):
        self.testing_class.highest_versions = {
            'ssl': 100,
            'sdk': 100,
            'waf': 100,
            'domain': 100,
            'purge': 100,
        }
        self.testing_class.proxy_server = {
            "ssl_cert_version": 99,
            "app_config_version": 100,
            "domain_config_version": 100,
            "waf_rule_version": 100,
            "purge_version": 100

        }
        check_list = self.testing_class.check_need_update_versions()

        self.assertEquals(
            check_list,
            {
                'ssl': True,
                'waf_sdk': False,
                'domain_purge': False
            }
        )

    def test_check_need_update_versions_low_sdk(self):
        self.testing_class.highest_versions = {
            'ssl': 100,
            'sdk': 100,
            'waf': 100,
            'domain': 100,
            'purge': 100,
        }
        self.testing_class.proxy_server = {
            "ssl_cert_version": 100,
            "app_config_version": 1,
            "domain_config_version": 100,
            "waf_rule_version": 100,
            "purge_version": 100

        }
        check_list = self.testing_class.check_need_update_versions()

        self.assertEquals(
            check_list,
            {
                'ssl': False,
                'waf_sdk': True,
                'domain_purge': False
            }
        )

    def test_check_need_update_versions_low_waf(self):
        self.testing_class.highest_versions = {
            'ssl': 100,
            'sdk': 100,
            'waf': 100,
            'domain': 100,
            'purge': 100,
        }
        self.testing_class.proxy_server = {
            "ssl_cert_version": 100,
            "app_config_version": 100,
            "domain_config_version": 100,
            "waf_rule_version": 1,
            "purge_version": 100

        }
        check_list = self.testing_class.check_need_update_versions()

        self.assertEquals(
            check_list,
            {
                'ssl': False,
                'waf_sdk': True,
                'domain_purge': False
            }
        )

    def test_check_need_update_versions_low_domain(self):
        self.testing_class.highest_versions = {
            'ssl': 100,
            'sdk': 100,
            'waf': 100,
            'domain': 100,
            'purge': 100,
        }
        self.testing_class.proxy_server = {
            "ssl_cert_version": 100,
            "app_config_version": 100,
            "domain_config_version": 1,
            "waf_rule_version": 100,
            "purge_version": 100

        }
        check_list = self.testing_class.check_need_update_versions()

        self.assertEquals(
            check_list,
            {
                'ssl': False,
                'waf_sdk': False,
                'domain_purge': True
            }
        )

    def test_check_need_update_versions_low_purge(self):
        self.testing_class.highest_versions = {
            'ssl': 100,
            'sdk': 100,
            'waf': 100,
            'domain': 100,
            'purge': 100,
        }
        self.testing_class.proxy_server = {
            "ssl_cert_version": 100,
            "app_config_version": 100,
            "domain_config_version": 100,
            "waf_rule_version": 100,
            "purge_version": 1

        }
        check_list = self.testing_class.check_need_update_versions()

        self.assertEquals(
            check_list,
            {
                'ssl': False,
                'waf_sdk': False,
                'domain_purge': True
            }
        )

    def test_check_installed_packages(self):
        server = Mock()
        server.check_install_package.return_value = True
        self.testing_class.check_installed_packages(server)
        server.check_install_package.assert_called()

    def test_check_installed_packages_not_installed(self):
        server = Mock()
        server.check_install_package.return_value = False
        # self.testing_class.check_installed_packages(server)
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_installed_packages,
            server
        )
        server.check_install_package.assert_called()


class TestNS1Class(TestAbstract):

    test_monitor = {
        'status': {
            'sjc': {
                'status': 'down',
                'since': 1513890023,
                'fail_set': [
                    'Failure for Rule: output contains this is a test',
                    'Connection error/Timeout'
                ]
            },
            'global': {
                'status': 'up', 'since': 1513890023, 'fail_set': ['sjc']
            }
        },
        'notify_list': None,
        'notify_repeat': 0,
        'notify_failback': True,
        'name': 'test-test2.host',
        'mute': False,
        'rules': [
            {
                'comparison': 'contains',
                'key': 'output',
                'value': 'this is a test'
            }
        ],
        'notes': None,
        'notify_delay': 0,
        'job_type': 'tcp',
        'notify_regional': False,
        'regions': ['sjc'],
        'active': True,
        'v2': True,
        'frequency': 60,
        'rapid_recheck': False,
        'policy': 'quorum',
        'region_scope': 'fixed',
        'config': {
            'response_timeout': 1000,
            'host': 'test-test2.host',
            'connect_timeout': 2000,
            'send': 'GET /test-cache.js HTTP/1.1\nHost: monitor.revsw.net\n\n',
            'port': 80
        },
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
        self.mongo_cli = pymongo.MongoClient(
            settings.MONGO_HOST, settings.MONGO_PORT
        )
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db['test_host']

        self.logger = mongo_logger.MongoLogger(
            'test_host', datetime.datetime.now().isoformat(),
            {
                "hostname": 'hostname',
                "ip": '111.111.111.111',
                "login": 'login',
                "password": 'passw',
            },
            self.logger_schema,
            self.current_server_state,
            self.logger_steps
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
        self.testing_class.delete_monitor('5678')

    def test_delete_monitor_fail(self):
        self.testing_class.monitor = Mock()
        self.testing_class.monitor.delete.side_effect = ResourceException(
            'error'
        )
        with self.assertRaises(DeploymentError):
            self.testing_class.delete_monitor('5678')

    def test_add_feed(self):
        raised_exception = False
        try:
            feed = self.testing_class.add_feed('1234', '5678')
        except DeploymentError as e:
            raised_exception = True
        self.assertTrue(raised_exception)

    def test_get_zone(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadZone.return_value = {'id': 1}
        result = self.testing_class.get_zone('zone_name')
        self.assertEquals(result, {'id': 1})
        self.testing_class.ns1.loadZone.assert_called_with('zone_name')

    def test_get_zone_error(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadZone.side_effect = ResourceException('error')
        self.assertRaises(
            DeploymentError,
            self.testing_class.get_zone,
            'zone_name'
        )
        self.testing_class.ns1.loadZone.assert_called_with('zone_name')

    def test_get_zone_zone_error(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadZone.side_effect = ZoneException('error')
        self.assertRaises(
            DeploymentError,
            self.testing_class.get_zone,
            'zone_name'
        )
        self.testing_class.ns1.loadZone.assert_called_with('zone_name')

    def test_add_a_record(self):
        zone = Mock()
        zone.add_A.return_value = "record"
        result = self.testing_class.add_a_record(zone, 'test-test')
        self.assertEquals(result, 'record')
        zone.add_A.assert_called()

    def test_add_a_record_zone_error(self):
        zone = Mock()
        zone.add_A.side_effect = ZoneException('error')
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_a_record,
            zone, 'test-test'
        )
        zone.add_A.assert_called()

    def test_add_a_record_resource_error(self):
        zone = Mock()
        zone.add_A.side_effect = ResourceException('error')
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_a_record,
            zone, 'test-test'
        )
        zone.add_A.assert_called()

    # def test_get_a_record(self):
    #     ns1.Record = Mock()
    #     ns1.Record.load.return_value = None
        # self.testing_class.get_a_record('zone_name', 'domain', 'a')

    def test_find_feed(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.list.return_value = [
            {
                'config': {
                    'jobid': 123
                },
                "id": 789
            }
        ]
        self.testing_class.ns1.datafeed.return_value = datafeed
        result = self.testing_class.find_feed(456, 123)
        self.assertEqual(result, 789)

    def test_find_feed_wrong_jobid(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.list.return_value = [
            {
                'config': {
                    'jobid': 456
                },
                "id": 789
            }
        ]
        self.testing_class.ns1.datafeed.return_value = datafeed
        result = self.testing_class.find_feed(456, 123)
        self.assertEqual(result, None)

    def test_find_feed_wrong_resource_error(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.list.side_effect = ResourceException(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_feed,
            456, 123
        )

    def test_find_feed_wrong_zone_error(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.list.side_effect = ZoneException(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_feed,
            456, 123
        )

    def test_find_feed_wrong_exception(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.list.side_effect = Exception(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_feed,
            456, 123
        )

    def test_get_feed(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.retrieve.return_value = 'feed'
        self.testing_class.ns1.datafeed.return_value = datafeed
        result = self.testing_class.get_feed(456, 123)
        self.assertEqual(result, 'feed')

    def test_get_feed_wrong_resource_error(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.retrieve.side_effect = ResourceException(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.get_feed,
            456, 123
        )

    def test_get_feed_wrong_zone_error(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.retrieve.side_effect = ZoneException(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.get_feed,
            456, 123
        )

    def test_get_feed_wrong_exception(self):
        self.testing_class.ns1 = Mock()
        datafeed = Mock()
        datafeed.retrieve.side_effect = Exception(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.get_feed,
            456, 123
        )

    def test_delete_feed(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.find_feed = Mock(return_value=123)
        datafeed = Mock()
        datafeed.delete.return_value = None
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.testing_class.delete_feed(456, 123)

    def test_delete_feed_no_feed(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.find_feed = Mock(return_value=None)
        datafeed = Mock()
        datafeed.delete.return_value = None
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.testing_class.delete_feed(456, 123)

    def test_delete_feed_wrong_resource_error(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.find_feed = Mock(return_value=123)
        datafeed = Mock()
        datafeed.delete.side_effect = ResourceException(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.delete_feed,
            456, 123
        )

    def test_delete_feed_wrong_zone_error(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.find_feed = Mock(return_value=123)
        datafeed = Mock()
        datafeed.delete.side_effect = ZoneException(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.delete_feed,
            456, 123
        )

    def test_delete_feed_wrong_exception(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.find_feed = Mock(return_value=123)
        datafeed = Mock()
        datafeed.delete.side_effect = Exception(1)
        self.testing_class.ns1.datafeed.return_value = datafeed
        self.assertRaises(
            DeploymentError,
            self.testing_class.delete_feed,
            456, 123
        )

    def test_check_record_answers(self):
        record = NS1Record()
        self.testing_class.logger = Mock()
        self.testing_class.get_feed = Mock(return_value={'data': {'up': True}})
        result = self.testing_class.check_record_answers(record)
        self.assertEqual(result, 1)

    def test_check_record_answers_not_up(self):
        record = NS1Record()
        self.testing_class.get_feed = Mock(return_value={'data': {'up': False}})
        result = self.testing_class.check_record_answers(record)
        self.assertEqual(result, 0)

    def test_add_answer(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadRecord.return_value = NS1Record()
        self.testing_class.add_answer(
            'zone', 'record_name', 'record_type',
            'answer_host', 'region', 'feed_id'
        )

    def test_add_answer_already_exist(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadRecord.return_value = NS1Record()
        self.testing_class.add_answer(
            'zone', 'record_name', 'record_type',
            '111.111.111.11', 'region', 'feed_id'
        )

    def test_add_answer_resource_error(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadRecord.side_effect = ResourceException(1)
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_answer,
            'zone', 'record_name', 'record_type',
            '111.111.111.11', 'region', 'feed_id'
        )

    def test_add_answer_zone_error(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadRecord.side_effect = ZoneException(1)
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_answer,
            'zone', 'record_name', 'record_type',
            '111.111.111.11', 'region', 'feed_id'
        )

    def test_add_answer_exception(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.loadRecord.side_effect = Exception(1)
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_answer,
            'zone', 'record_name', 'record_type',
            '111.111.111.11', 'region', 'feed_id'
        )


class TestAbstractSequence(TestAbstract):
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
            'test_host', datetime.datetime.now().isoformat(),
            {
                "hostname": 'hostname',
                "ip": '111.111.111.111',
                "login": 'login',
                "password": 'passw',
            },
            self.logger_schema,
            self.current_server_state,
            self.logger_steps
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
            "login": "login",
            "password": "password"

        }

        self.args = Objectview(args_dict)
        abs_sequence.InfraDBAPI = MockedInfraDB
        abs_sequence.NagiosServer = MockedNagiosClass
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") \
                as ns1_mock:
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
        self.testing_class.step_sequence = ['another_step', ]
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

        self.logger = Mock()
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
            "environment": "prod",
        }

        deploy_sequence.CDSAPI = Mock()
        deploy_sequence.Cacti = Mock()
        args = Objectview(args_dict)
        abs_sequence.InfraDBAPI = MockedInfraDB
        deploy_sequence.ServerState = MockedServerClass
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") \
                as ns1_mock:
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
        self.testing_class.ns1.add_a_record.return_value = {'id': 123}

        self.testing_class.add_ns1_a_record()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.add_a_record.assert_called()

    def test_radd_ns1_a_record_wrong_record(self):
        self.testing_class.ns1 = Mock()
        ns1_record = NS1Record()
        ns1_record.data['answers'] = [
            {"answer": [u'222.111.111.11', ], "id": "1213"}
        ]
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
        self.testing_class.add_ns1_a_record()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.add_a_record.assert_not_called()

    def test_radd_ns1_a_record_record_with_oter_ip(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = NS1Record(
            ip=u'222.222.222.222'
        )
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

    def test_check_hostname_step(self):
        self.testing_class.server = Mock()
        self.testing_class.server.check_hostname.return_value = "test-host.test.test"
        self.testing_class.check_hostname_step()
        self.testing_class.server.check_hostname.assert_called()
        self.testing_class.server.reboot.assert_not_called()

    def test_check_hostname_step_wrong(self):
        self.testing_class.server = Mock()
        self.testing_class.server.check_hostname.return_value = "wrong_test-host.test.test"
        self.testing_class.check_hostname_step()
        self.testing_class.server.check_hostname.assert_called()
        self.testing_class.server.reboot.assert_called()

    def test_run_puppet(self):
        self.testing_class.server = Mock()
        self.testing_class.server.run_puppet.return_value = 0
        self.testing_class.sign_ssl_puppet = Mock()
        self.testing_class.run_puppet()
        self.testing_class.sign_ssl_puppet.assert_not_called()
        self.testing_class.server.run_puppet.assert_called()

    def test_run_puppet_not_first_run(self):
        self.testing_class.server = Mock()
        self.testing_class.server.run_puppet.return_value = 1
        self.testing_class.sign_ssl_puppet = Mock()
        self.testing_class.run_puppet()
        self.testing_class.sign_ssl_puppet.assert_called()
        self.testing_class.server.run_puppet.assert_called()

    def test_update_fw_rules(self):
        connect = Mock()
        connect.exec_command.return_value = [
            1, MockedExecOutput(['test_server', ]), 1
        ]
        self.testing_class.connect_to_serv = Mock(return_value=connect)
        self.testing_class.execute_command = Mock(return_value=(0, 'output'))
        self.testing_class.update_fw_rules()

    def test_sign_ssl_puppet(self):
        connect = Mock()
        connect.exec_command.return_value = [
            1, MockedExecOutput(['test_server', ]), 1
        ]
        self.testing_class.connect_to_serv = Mock(return_value=connect)
        self.testing_class.sign_ssl_puppet()

    def test_sign_ssl_puppet_wrong_status(self):
        connect = Mock()
        connect.exec_command.return_value = [
            1, MockedExecOutput(['test_server', ], return_status=1), 1
        ]
        self.testing_class.connect_to_serv = Mock(return_value=connect)
        self.assertRaises(
            DeploymentError,
            self.testing_class.sign_ssl_puppet
        )

    def test_add_to_nagios(self):
        self.testing_class.nagios = Mock()
        self.testing_class.nagios.check_nagios_config.return_value = 0
        self.testing_class.add_to_nagios()
        self.testing_class.nagios.check_nagios_config.assert_called_once()
        self.testing_class.nagios.create_config_file.assert_called_once()
        self.testing_class.nagios.send_config_to_server.assert_called_once()
        self.testing_class.nagios.reload_nagios.assert_called_once()

    def test_add_to_nagios_not_nagios_config(self):
        self.testing_class.nagios = Mock()
        self.testing_class.nagios.check_nagios_config.return_value = 1
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_to_nagios
        )
        self.testing_class.nagios.check_nagios_config.assert_called_once()
        self.testing_class.nagios.create_config_file.assert_called_once()
        self.testing_class.nagios.send_config_to_server.assert_called_once()
        self.testing_class.nagios.reload_nagios.assert_not_called()

    def test_add_to_pssh_file(self):
        connect = Mock()
        connect.exec_command.return_value = [
            1, MockedExecOutput([]), 1
        ]
        self.testing_class.connect_to_serv = Mock(return_value=connect)
        self.testing_class.add_to_pssh_file()
        connect.exec_command.assert_called_with("sudo echo %s >> %s" % (
            'test-host', settings.PSSH_FILE_PATH
        ))

    def test_add_to_pssh_file_already_added(self):
        connect = Mock()
        connect.exec_command.return_value = [
            1, MockedExecOutput(['test_server', ]), 1
        ]
        self.testing_class.connect_to_serv = Mock(return_value=connect)
        self.testing_class.add_to_pssh_file()

    @patch('server_deploy.DeploySequence')
    def test_main_deployment_sequence(self, depl_seq):
        # test for check that all of arguments is parsed
        deploy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        deploy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        deploy_sequence.argparse.ArgumentParser = mocked_args
        deploy_sequence.sys = Mock()
        deploy_sequence.main()
        test_data = [
            '--host_name', '--zone_name', '--IP', '--record_type',
            '--login', '--password', '--cert', '--hosting',
            '--server_group', '--environment', '--dns_balancing_name',
            '--first_step', '--number_of_steps_to_execute',
            '--disable_infradb_ssl'
        ]
        self.assertEqual(test_data, mocked_args.added_arguments)

    @patch('server_deploy.DeploySequence')
    def test_main_check_server_status_required_list(self, depl_seq):
        # test for check that all of arguments is parsed
        deploy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        deploy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        deploy_sequence.argparse.ArgumentParser = mocked_args
        deploy_sequence.sys = Mock()
        deploy_sequence.main()
        test_data = ['--host_name', '--IP']

        print mocked_args.required_arguments
        self.assertEqual(test_data, mocked_args.required_arguments)

    @patch('server_deploy.DeploySequence')
    def test_main_check_server_status_default_values(self, depl_seq):
        # test for check that all of arguments is parsed
        deploy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        deploy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        deploy_sequence.argparse.ArgumentParser = mocked_args
        deploy_sequence.sys = Mock()
        deploy_sequence.main()
        test_data = {
            '--record_type': 'A',
            '--server_group': '5588823fbde7a0d00338ce8d',
            '--login': 'robot',
            '--zone_name': 'attested.club',
            '--environment': 'prod',
            '--hosting': 'HE',
            '--first_step': 'change_password'
        }

        print mocked_args.default_values
        self.assertEqual(test_data, mocked_args.default_values)

    @patch('server_deploy.DeploySequence')
    def test_main_check_server_status_step_choices(self, depl_seq):
        # test for check that all of arguments is parsed
        deploy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        deploy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        deploy_sequence.argparse.ArgumentParser = mocked_args
        deploy_sequence.sys = Mock()
        deploy_sequence.main()
        test_data = [
            'change_password', 'check_server_consistency',
            'check_hostname', 'add_ns1_a_record', 'add_to_infradb',
            'update_fw_rules', 'install_puppet', 'run_puppet',
            'add_to_cds', 'add_to_nagios', 'add_ns1_monitor',
            'add_ns1_balancing_rule', 'add_to_pssh_file', 'add_to_cacti'
        ]

        print mocked_args.step_choices
        self.assertEqual(test_data, mocked_args.step_choices)

    def test_check_server_consistency(self):
        self.testing_class.server = Mock()
        self.testing_class.check_server_consistency()
        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    def test_change_password(self):
        self.testing_class.server = Mock()
        self.testing_class.change_password()
        self.testing_class.server.change_password.assert_called()

    @patch("settings.PROXYY_RESTART_WAITING_TIME", 0)
    def test_deploy_cds(self):
        # cds = Mock()
        self.testing_class.cds.check_server_exist.return_value = True
        self.testing_class.cds.check_server_in_group.return_value = True
        self.testing_class.cds.check_need_update_versions.return_value = {
            'ssl': False,
            'waf_sdk': False,
            'domain_purge': False
        }
        self.testing_class.cds.add_server.return_value = True
        self.testing_class.cds.monitor_ssl_configuration.return_value = True
        self.testing_class.cds.update_server.return_value = True
        self.testing_class.cds.monitor_waf_and_sdk_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        self.testing_class.cds.server_group.return_value = True
        self.testing_class.cds.monitor_purge_and_domain_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        # deploy_sequence.CDSAPI = cds
        self.testing_class.server = Mock()
        self.testing_class.deploy_cds()
        self.testing_class.cds.check_server_exist.assert_called()
        self.testing_class.cds.check_server_in_group.assert_called()
        self.testing_class.cds.check_need_update_versions.assert_called()
        self.testing_class.cds.add_server.assert_not_called()
        self.testing_class.cds.monitor_ssl_configuration.assert_not_called()
        self.testing_class.cds.update_server.assert_not_called()
        self.testing_class.cds.monitor_waf_and_sdk_configuration.assert_not_called()
        self.testing_class.cds.add_server_to_group.assert_not_called()
        self.testing_class.cds.monitor_purge_and_domain_configuration.assert_not_called()

    @patch("settings.PROXYY_RESTART_WAITING_TIME", 0)
    def test_deploy_cds_server_not_exist(self):
        # cds = Mock()
        self.testing_class.cds.check_server_exist.return_value = False
        self.testing_class.cds.check_server_in_group.return_value = True
        self.testing_class.cds.add_server.return_value = True
        self.testing_class.cds.monitor_ssl_configuration.return_value = True
        self.testing_class.cds.update_server.return_value = True
        self.testing_class.cds.monitor_waf_and_sdk_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        self.testing_class.cds.server_group.return_value = True
        self.testing_class.cds.monitor_purge_and_domain_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        # deploy_sequence.CDSAPI = cds
        self.testing_class.server = Mock()
        self.testing_class.deploy_cds()
        self.testing_class.cds.check_server_exist.assert_called()
        self.testing_class.cds.check_server_in_group.assert_not_called()
        self.testing_class.cds.check_need_update_versions.assert_not_called()
        self.testing_class.cds.add_server.assert_called()
        self.testing_class.cds.monitor_ssl_configuration.assert_called()
        self.testing_class.cds.update_server.assert_called()
        self.testing_class.cds.monitor_waf_and_sdk_configuration.assert_called()
        self.testing_class.cds.add_server_to_group.assert_called()
        self.testing_class.cds.monitor_purge_and_domain_configuration.assert_called()

    @patch("settings.PROXYY_RESTART_WAITING_TIME", 0)
    def test_deploy_cds_need_update_ssl(self):
        # cds = Mock()
        self.testing_class.cds.check_server_exist.return_value = True
        self.testing_class.cds.check_server_in_group.return_value = True
        self.testing_class.cds.check_need_update_versions.return_value = {
            'ssl': True,
            'waf_sdk': False,
            'domain_purge': False
        }
        self.testing_class.cds.add_server.return_value = True
        self.testing_class.cds.monitor_ssl_configuration.return_value = True
        self.testing_class.cds.update_server.return_value = True
        self.testing_class.cds.monitor_waf_and_sdk_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        self.testing_class.cds.server_group.return_value = True
        self.testing_class.cds.monitor_purge_and_domain_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        # deploy_sequence.CDSAPI = cds
        self.testing_class.server = Mock()
        self.testing_class.deploy_cds()
        self.testing_class.cds.check_server_exist.assert_called()
        self.testing_class.cds.check_server_in_group.assert_called()
        self.testing_class.cds.check_need_update_versions.assert_called()
        self.testing_class.cds.add_server.assert_not_called()
        self.testing_class.cds.monitor_ssl_configuration.assert_called()
        self.testing_class.cds.update_server.assert_not_called()
        self.testing_class.cds.monitor_waf_and_sdk_configuration.assert_not_called()
        self.testing_class.cds.add_server_to_group.assert_not_called()
        self.testing_class.cds.monitor_purge_and_domain_configuration.assert_not_called()

    @patch("settings.PROXYY_RESTART_WAITING_TIME", 0)
    def test_deploy_cds_need_update_waf_sdk(self):
        # cds = Mock()
        self.testing_class.cds.check_server_exist.return_value = True
        self.testing_class.cds.check_server_in_group.return_value = True
        self.testing_class.cds.check_need_update_versions.return_value = {
            'ssl': False,
            'waf_sdk': True,
            'domain_purge': False
        }
        self.testing_class.cds.add_server.return_value = True
        self.testing_class.cds.monitor_ssl_configuration.return_value = True
        self.testing_class.cds.update_server.return_value = True
        self.testing_class.cds.monitor_waf_and_sdk_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        self.testing_class.cds.server_group.return_value = True
        self.testing_class.cds.monitor_purge_and_domain_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        # deploy_sequence.CDSAPI = cds
        self.testing_class.server = Mock()
        self.testing_class.deploy_cds()
        self.testing_class.cds.check_server_exist.assert_called()
        self.testing_class.cds.check_server_in_group.assert_called()
        self.testing_class.cds.check_need_update_versions.assert_called()
        self.testing_class.cds.add_server.assert_not_called()
        self.testing_class.cds.monitor_ssl_configuration.assert_not_called()
        self.testing_class.cds.update_server.assert_called()
        self.testing_class.cds.monitor_waf_and_sdk_configuration.assert_called()
        self.testing_class.cds.add_server_to_group.assert_not_called()
        self.testing_class.cds.monitor_purge_and_domain_configuration.assert_not_called()

    @patch("settings.PROXYY_RESTART_WAITING_TIME", 0)
    def test_deploy_cds_need_update_domain_purge(self):
        # cds = Mock()
        self.testing_class.cds.check_server_exist.return_value = True
        self.testing_class.cds.check_server_in_group.return_value = True
        self.testing_class.cds.check_need_update_versions.return_value = {
            'ssl': False,
            'waf_sdk': False,
            'domain_purge': True
        }
        self.testing_class.cds.add_server.return_value = True
        self.testing_class.cds.monitor_ssl_configuration.return_value = True
        self.testing_class.cds.update_server.return_value = True
        self.testing_class.cds.monitor_waf_and_sdk_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        self.testing_class.cds.server_group.return_value = True
        self.testing_class.cds.monitor_purge_and_domain_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        # deploy_sequence.CDSAPI = cds
        self.testing_class.server = Mock()
        self.testing_class.deploy_cds()
        self.testing_class.cds.check_server_exist.assert_called()
        self.testing_class.cds.check_server_in_group.assert_called()
        self.testing_class.cds.check_need_update_versions.assert_called()
        self.testing_class.cds.add_server.assert_not_called()
        self.testing_class.cds.monitor_ssl_configuration.assert_not_called()
        self.testing_class.cds.update_server.assert_called()
        self.testing_class.cds.monitor_waf_and_sdk_configuration.assert_not_called()
        self.testing_class.cds.add_server_to_group.assert_not_called()
        self.testing_class.cds.monitor_purge_and_domain_configuration.assert_called()

    @patch("settings.PROXYY_RESTART_WAITING_TIME", 0)
    def test_deploy_cds_not_in_group(self):
        # cds = Mock()
        self.testing_class.cds.check_server_exist.return_value = True
        self.testing_class.cds.check_server_in_group.return_value = False
        self.testing_class.cds.check_need_update_versions.return_value = {
            'ssl': False,
            'waf_sdk': False,
            'domain_purge': False
        }
        self.testing_class.cds.add_server.return_value = True
        self.testing_class.cds.monitor_ssl_configuration.return_value = True
        self.testing_class.cds.update_server.return_value = True
        self.testing_class.cds.monitor_waf_and_sdk_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        self.testing_class.cds.server_group.return_value = True
        self.testing_class.cds.monitor_purge_and_domain_configuration.return_value = True
        self.testing_class.cds.add_server_to_group.return_value = True
        # deploy_sequence.CDSAPI = cds
        self.testing_class.server = Mock()
        self.testing_class.deploy_cds()
        self.testing_class.cds.check_server_exist.assert_called()
        self.testing_class.cds.check_server_in_group.assert_called()
        self.testing_class.cds.check_need_update_versions.assert_called()
        self.testing_class.cds.add_server.assert_not_called()
        self.testing_class.cds.monitor_ssl_configuration.assert_not_called()
        self.testing_class.cds.update_server.assert_not_called()
        self.testing_class.cds.monitor_waf_and_sdk_configuration.assert_not_called()
        self.testing_class.cds.add_server_to_group.assert_called()
        self.testing_class.cds.monitor_purge_and_domain_configuration.assert_not_called()

    def test_add_to_cacti(self):
        self.testing_class.cacti = Mock()
        self.testing_class.cacti.add_device.return_value = 1
        self.testing_class.cacti.find_graph.return_value = None
        self.testing_class.cacti.add_graph.return_value = 1
        self.testing_class.cacti.add_graph_to_tree.return_value = 1
        self.testing_class.add_to_cacti()
        self.testing_class.cacti.add_device.assert_called_once()
        self.testing_class.cacti.find_graph.assert_called()
        self.testing_class.cacti.add_graph.assert_called()
        self.testing_class.cacti.add_graph_to_tree.assert_called()

    def test_add_to_cacti_graph_exist(self):
        self.testing_class.cacti = Mock()
        self.testing_class.cacti.add_device.return_value = 1
        self.testing_class.cacti.find_graph.return_value = 1
        self.testing_class.cacti.add_graph.return_value = 1
        self.testing_class.cacti.add_graph_to_tree.return_value = 1
        self.testing_class.add_to_cacti()
        self.testing_class.cacti.add_device.assert_called_once()
        self.testing_class.cacti.find_graph.assert_called()
        self.testing_class.cacti.add_graph.assert_not_called()
        self.testing_class.cacti.add_graph_to_tree.assert_called()

    def test_add_to_cacti_add_device_error(self):
        self.testing_class.cacti = Mock()
        self.testing_class.cacti.add_device.side_effect = DeploymentError('error')
        self.testing_class.cacti.find_graph.return_value = 1
        self.testing_class.cacti.add_graph.return_value = 1
        self.testing_class.cacti.add_graph_to_tree.return_value = 1
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_to_cacti
        )
        self.testing_class.cacti.add_device.assert_called_once()
        self.testing_class.cacti.find_graph.assert_not_called()
        self.testing_class.cacti.add_graph.assert_not_called()
        self.testing_class.cacti.add_graph_to_tree.assert_not_called()


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
            'test_host', datetime.datetime.now().isoformat(),
            {
                "hostname": 'hostname',
                "ip": '111.111.111.111',
                "login": 'login',
                "password": 'passw',
            },
            self.logger_schema,
            self.current_server_state,
            self.logger_steps
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
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") \
                as ns1_mock:
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
        self.testing_class.ns1.delete_feed.assert_called_once_with(
            settings.NS1_DATA_SOURCE_ID, 1
        )
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
        destroy_sequence.Proxy = Mock()
        destroy_sequence.Proxy.wait_low_traffic.return_value = None
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = NS1Record()
        self.testing_class.ns1.check_record_answers.return_value = 31

        self.testing_class.remove_ns1_balancing_rule()

        self.testing_class.ns1.get_a_record.assert_called()

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
        self.testing_class.ns1.get_a_record.return_value = NS1Record(
            ip='111.111.111.11'
        )
        self.testing_class.ns1.check_record_answers.return_value = 20
        self.assertRaises(
            DeploymentError,
            self.testing_class.remove_ns1_balancing_rule
        )

        self.testing_class.ns1.get_a_record.assert_called()

    @patch("settings.NS1_AFTER_ANSWER_DELETING_WAIT_TIME", 0)
    def test_remove_ns1_balancing_rule_ip_not_found(self):
        self.testing_class.ns1 = Mock()
        ns1_record = NS1Record()
        ns1_record.data['answers'] = [
            {"answer": ['222.111.111.11', ], "id": "1213"}
        ]
        self.testing_class.ns1.get_a_record.return_value = ns1_record
        self.testing_class.ns1.check_record_answers.return_value = 31

        self.testing_class.remove_ns1_balancing_rule()

        self.testing_class.ns1.get_a_record.assert_called()
        self.testing_class.ns1.check_record_answers.assert_not_called()

    def test_remove_from_pssh_file(self):
        connection = Mock()
        self.testing_class.connect_to_serv = Mock(return_value=connection)
        connection.exec_command.return_value = [
            1, MockedExecOutput(['test_server', ]), 1
        ]
        self.testing_class.remove_from_pssh_file()
        connection.exec_command.assert_called_with("sudo sed '%s' %s" % (
            'test-host', settings.PSSH_FILE_PATH
        ))

    def test_remove_from_pssh_file_no_file(self):
        connection = Mock()
        self.testing_class.connect_to_serv = Mock(return_value=connection)
        connection.exec_command.return_value = [
            1, MockedExecOutput([ ]), 1
        ]
        self.testing_class.remove_from_pssh_file()
        connection.exec_command.assert_called_once_with('grep "%s" %s' % (
            'test-host', settings.PSSH_FILE_PATH
        ))

    def test_remove_from_puppet(self):
        connection = Mock()
        self.testing_class.connect_to_serv = Mock(return_value=connection)
        connection.exec_command.return_value = [
            1, MockedExecOutput([], return_status=0), 1
        ]
        self.testing_class.remove_from_puppet()
        connection.exec_command.assert_called_once_with(
            "sudo puppet cert clean %s" % self.host_name
        )

    def test_remove_from_puppet_wrong_answer(self):
        connection = Mock()
        self.testing_class.connect_to_serv = Mock(return_value=connection)
        connection.exec_command.return_value = [
            1, MockedExecOutput([], return_status=1), 1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.remove_from_puppet
        )
        connection.exec_command.assert_called_once_with(
            "sudo puppet cert clean %s" % self.host_name
        )

    @patch('destroying_server.DestroySequence')
    def test_main_destroy_sequence(self, dest_seq):
        # test for check that all of arguments is parsed
        destroy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        destroy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        destroy_sequence.argparse.ArgumentParser = mocked_args

        destroy_sequence.sys = Mock()
        destroy_sequence.main()
        test_data = [
            '--host_name', '--zone_name', '--IP', '--record_type',
            '--login', '--password', '--hosting', '--server_group',
            '--environment', '--dns_balancing_name', '--first_step',
            '--number_of_steps_to_execute', '--disable_infradb_ssl'
        ]
        self.assertEqual(test_data, mocked_args.added_arguments)

    @patch('destroying_server.DestroySequence')
    def test_main_check_server_status_required_list(self, dest_seq):
        # test for check that all of arguments is parsed
        destroy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        destroy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        destroy_sequence.argparse.ArgumentParser = mocked_args

        destroy_sequence.sys = Mock()
        destroy_sequence.main()
        test_data = ['--host_name', '--IP']
        self.assertEqual(test_data, mocked_args.required_arguments)

    @patch('destroying_server.DestroySequence')
    def test_main_check_server_status_default_values(self, dest_seq):
        # test for check that all of arguments is parsed
        destroy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        destroy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        destroy_sequence.argparse.ArgumentParser = mocked_args

        destroy_sequence.sys = Mock()
        destroy_sequence.main()
        test_data = {
            '--record_type': 'A',
            '--server_group': '5588823fbde7a0d00338ce8d',
            '--login': 'robot', '--zone_name': 'attested.club',
            '--environment': 'prod',
            '--hosting': 'HE',
            '--first_step': 'remove_ns1_balancing_rule'
        }

        print mocked_args.default_values
        self.assertEqual(test_data, mocked_args.default_values)

    @patch('destroying_server.DestroySequence')
    def test_main_check_server_status_step_choices(self, dest_seq):
        # test for check that all of arguments is parsed
        destroy_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        destroy_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        destroy_sequence.argparse.ArgumentParser = mocked_args

        destroy_sequence.sys = Mock()
        destroy_sequence.main()
        test_data = [
            'remove_ns1_a_record', 'remove_from_nagios', 'remove_from_cds',
            'remove_ns1_monitor', 'remove_from_infradb', 'remove_from_puppet',
            'remove_ns1_balancing_rule', 'remove_from_pssh_file'
        ]
        self.assertEqual(test_data, mocked_args.step_choices)


class TestServerState(TestAbstract):
    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
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

        self.logger = Mock()
        self.mocked_ns1_class = MockNSONE(apikey="1234")
        self.mocked_ns1_monitors = NS1MonitorMock()
        self.host_name = 'test-test1.host'
        self.ip = '111.111.111.111'
        self.connection = Mock()
        server_state.paramiko = Mock()
        server_state.paramiko.SSHClient.connect.return_value = self.connection
        server_state.paramiko.RSAKey.from_private_key_file.return_value = 'key'

        self.testing_class = ServerState(
            self.host_name, 'login', 'password', self.logger
        )

        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_check_hostname(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test_hostname.test.test', ]), '3'
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
            ]), '3'
        ]
        ret_data = self.testing_class.check_install_package('test_package')
        self.assertTrue(ret_data)
        self.testing_class.client.exec_command.assert_called_with(
            "dpkg -s test_package"
        )

    def test_check_install_package_not_installed(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['ok', 'not installed\n', ]), '3'
        ]
        ret_data = self.testing_class.check_install_package('test_package')
        self.assertFalse(ret_data)
        self.testing_class.client.exec_command.assert_called_with(
            "dpkg -s test_package"
        )

    def test_check_system_version(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'DISTRIB_RELEASE=14.04',
            ]), '3'
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
            ]), '3'
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
            ]), '3'
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
            ]), '3'
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
            ], return_status=1), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.execute_command_with_log,
            'command'
        )
        self.testing_class.client.exec_command.assert_called_with(
            'command'
        )

    def test_execute_command_with_log_wrong_status_without_check(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ], return_status=1), '3'
        ]
        ret_data = self.testing_class.execute_command_with_log(
            'command', check_status=False
        )
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
        self.testing_class.check_ram_size()
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
        self.testing_class.check_hw_architecture()
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
        self.testing_class.check_os_version()
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
                '1000 packets transmitted, 1000 received, '
                '0% packet loss, time 13347ms',
            ]), '3'
        ]
        self.testing_class.check_ping_8888()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo ping -f -c 1000 8.8.8.8"
        )

    def test_check_ping_8888_packet_loss(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                '1000 packets transmitted, 1000 received, '
                '1% packet loss, time 13347ms',
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
        self.testing_class.check_free_space()
        self.testing_class.client.exec_command.assert_called_with(
            "df"
        )

    def test_check_free_space_not_enouph(self):
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
        self.testing_class.remove_puppet()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo rm -r /var/lib/puppet/ssl"
        )

    def test_remove_puppet_wrong_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test'], return_status=1), '3'
        ]
        self.testing_class.remove_puppet()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo rm -r /var/lib/puppet/ssl"
        )

    def test_configure_puppet(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput(['test']), '3'
        ]
        self.testing_class.configure_puppet()
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

    def test_change_password(self):

        self.testing_class.generate_password = Mock(return_value='test_pass')
        self.testing_class.client = Mock()
        chan = Mock()
        chan.send.return_value = None
        self.testing_class.client.invoke_shell.return_value = chan
        self.testing_class.wait_for_state = Mock(return_value=None)
        self.testing_class.change_password('old_pass')
        # chan.send.assert_called_with('test_pass\n')
        # self.testing_class.client.invoke_shell.assert_called()
        # self.testing_class.wait_for_state.assert_called()

    def test_wait_for_state(self):
        chan =  Mock()
        chan.recv.return_value = 'other_data expected_value other_data'
        self.testing_class.wait_for_state(chan, 'expected_value')
        chan.recv.assert_called()

    def test_wait_for_state_no_value(self):
        chan =  Mock()
        chan.recv.return_value = 'other_data wrong_value other_data'
        self.assertRaises(
            DeploymentError,

            self.testing_class.wait_for_state,
            chan, 'expected_value'
        )
        chan.recv.assert_called()

    def test_generate_password(self):
        self.testing_class.generate_password()

    def test_check_traffic(self):
        test_data = [
            '{"response": 200, "clientip": "111.111.111.111"}',
            '{"response": 200, "clientip": "222.222.222.222"}',
            '{"response": 200, "clientip": "333.333.333.333"}',
        ]
        self.testing_class.client = Mock()
        logfile = Mock()
        logfile.readlines.return_value = test_data
        transport = Mock()
        transport.open.return_value = logfile
        self.testing_class.client.open_sftp.return_value = transport
        result = self.testing_class.check_traffic()
        transport.open.assert_called_with(
            '/var/log/nginx/revsw_nginx_access_json.log'
        )
        self.assertEqual(result, 3)

    def test_check_traffic_has_error(self):
        test_data = [
            '{"response": 200, "clientip": "111.111.111.111"}',
            '{"response": 500, "clientip": "222.222.222.222"}',
            '{"response": 200, "clientip": "333.333.333.333"}',
        ]
        self.testing_class.client = Mock()
        logfile = Mock()
        logfile.readlines.return_value = test_data
        transport = Mock()
        transport.open.return_value = logfile
        self.testing_class.client.open_sftp.return_value = transport
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_traffic
        )
        transport.open.assert_called_with(
            '/var/log/nginx/revsw_nginx_access_json.log'
        )

    def test_check_traffic_response_more_599(self):
        test_data = [
            '{"response": 200, "clientip": "111.111.111.111"}',
            '{"response": 601, "clientip": "222.222.222.222"}',
            '{"response": 200, "clientip": "333.333.333.333"}',
        ]
        self.testing_class.client = Mock()
        logfile = Mock()
        logfile.readlines.return_value = test_data
        transport = Mock()
        transport.open.return_value = logfile
        self.testing_class.client.open_sftp.return_value = transport
        result = self.testing_class.check_traffic()
        transport.open.assert_called_with(
            '/var/log/nginx/revsw_nginx_access_json.log'
        )
        self.assertEqual(result, 3)

    def test_check_traffic_not_all_ip_unique(self):
        test_data = [
            '{"response": 200, "clientip": "111.111.111.111"}',
            '{"response": 200, "clientip": "222.222.222.222"}',
            '{"response": 200, "clientip": "111.111.111.111"}',
        ]
        self.testing_class.client = Mock()
        logfile = Mock()
        logfile.readlines.return_value = test_data
        transport = Mock()
        transport.open.return_value = logfile
        self.testing_class.client.open_sftp.return_value = transport
        result = self.testing_class.check_traffic()
        transport.open.assert_called_with(
            '/var/log/nginx/revsw_nginx_access_json.log'
        )
        self.assertEqual(result, 2)

    def test_check_traffic_wrong_json(self):
        test_data = [
            '{"response": 200, "clientip": "111.111.111.111}',
            '{"response": 500, "clientip": "222.222.222.222"}',
            '{"response": 200, "clientip": "333.333.333.333"}',
        ]
        self.testing_class.client = Mock()
        logfile = Mock()
        logfile.readlines.return_value = test_data
        transport = Mock()
        transport.open.return_value = logfile
        self.testing_class.client.open_sftp.return_value = transport
        self.assertRaises(
            DeploymentError,
            self.testing_class.check_traffic
        )
        transport.open.assert_called_with(
            '/var/log/nginx/revsw_nginx_access_json.log'
        )


class TestNagiosServer(TestAbstract):
    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
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

        self.logger = Mock()
        for handler in nagios_deploy.logger.handlers:
            if isinstance(handler, MongoDBHandler):
                handler.add_mongo_logger(self.logger)
        self.host_name = 'test-test1.host'
        self.short_host = 'test-test1'
        self.connection = Mock()
        self.nagios_mock = Mock()
        nagios_deploy.paramiko = Mock()
        nagios_deploy.paramiko.SSHClient.connect.return_value = self.connection
        nagios_deploy.paramiko.RSAKey.from_private_key_file.return_value = 'key'
        nagios_deploy.Nagios = self.nagios_mock

        self.testing_class = nagios_deploy.NagiosServer(
            self.host_name, self.logger, self.short_host
        )

        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    @patch("settings.NAGIOS_FORCING_CHECK_SERVICES_WAIT_TIME", 0)
    @patch("settings.IGNORE_NAGIOS_SERVICES", ["ignore_service", ])
    def test_check_services_status(self):
        self.testing_class.nagios_api = Mock()
        self.testing_class.nagios_api.get_services_by_host.return_value = {
            'test_service1': {
                'current_state': "0",
            },
            "ignore_service": {
                'current_state': "0",
            },
        }
        self.testing_class.check_services_status()
        self.testing_class.client.exec_command.get_services_by_host(
            self.short_host
        )

    @patch("settings.NAGIOS_FORCING_CHECK_SERVICES_WAIT_TIME", 0)
    @patch("settings.IGNORE_NAGIOS_SERVICES", ["ignore_service", ])
    def test_check_services_status_not_up_service(self):
        self.testing_class.nagios_api = Mock()
        self.testing_class.nagios_api.get_services_by_host.return_value = {
            'test_service1': {
                'current_state': "1",
            },
            "ignore_service": {
                'current_state': "0",
            },
        }
        self.assertRaises(
            DeploymentError, self.testing_class.check_services_status
        )
        self.testing_class.client.exec_command.get_services_by_host(
            self.short_host
        )

    @patch("settings.NAGIOS_FORCING_CHECK_SERVICES_WAIT_TIME", 0)
    @patch("settings.IGNORE_NAGIOS_SERVICES", ["ignore_service", ])
    def test_check_services_status_ignoring_service_not_up(self):
        self.testing_class.nagios_api = Mock()
        self.testing_class.nagios_api.get_services_by_host.return_value = {
            'test_service1': {
                'current_state': "0",
            },
            "ignore_service": {
                'current_state': "1",
            },
        }
        self.testing_class.check_services_status()
        self.testing_class.client.exec_command.get_services_by_host(
            self.short_host
        )

    def test_execute_command_with_log(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ]), '3'
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
            ], return_status=1), '3'
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.execute_command_with_log,
            'command'
        )
        self.testing_class.client.exec_command.assert_called_with(
            'command'
        )

    def test_execute_command_with_log_wrong_status_without_check(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            '1', MockedExecOutput([
                'wrong_str',
            ], return_status=1), '3'
        ]
        ret_data = self.testing_class.execute_command_with_log(
            'command', check_status=False
        )
        self.assertEqual(ret_data, 1)
        self.testing_class.client.exec_command.assert_called_with(
            'command'
        )

    def test_create_config_file(self):
        data = {
            'host_name': self.short_host,
            "ip": '111.111.111.111',
            "location_code": "loc"
        }
        self.testing_class.create_config_file(data)
        self.assertTrue(os.path.exists('/tmp/%s.cfg' % self.short_host))

    def test_delete_config_file(self):
        self.testing_class.execute_command_with_log = Mock()
        self.testing_class.delete_config_file()

        self.testing_class.execute_command_with_log.assert_called_with("sudo rm %s" % os.path.join(
                settings.NAGIOS_CFG_PATH,
                '%s.cfg' % self.short_host
            ),
            check_status=False)

    def test_reload_nagios(self):
        self.testing_class.execute_command_with_log = Mock(return_value=0)
        self.testing_class.reload_nagios()
        self.testing_class.execute_command_with_log.assert_called_with(
            "sudo /etc/init.d/nagios reload"
        )

    def test_reload_nagios_error(self):
        self.testing_class.execute_command_with_log = Mock(return_value=1)
        self.assertRaises(
            DeploymentError,
            self.testing_class.reload_nagios
        )
        self.testing_class.execute_command_with_log.assert_called_with(
            "sudo /etc/init.d/nagios reload"
        )

    def test_check_nagios_config(self):
        self.testing_class.execute_command_with_log = Mock()
        self.testing_class.check_nagios_config()
        self.testing_class.execute_command_with_log.assert_called_with(
            "sudo /etc/init.d/nagios checkconfig"
        )


class TestCheckSequence(TestAbstract):
    @patch("settings.CDS_URL", 'http://localhost:8000/api/')
    @patch("settings.MONGO_DB_NAME", 'test_database')
    def setUp(self):
        # mocking mogo db variables for conecting to test  database
        # settings.MONGO_DB_NAME = 'test_database'
        connection = Mock()
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
            'test_host', datetime.datetime.now().isoformat(),
            {
                "hostname": 'hostname',
                "ip": '111.111.111.111',
                "login": 'login',
                "password": 'passw',
            },
            self.logger_schema,
            self.current_server_state,
            self.logger_steps

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
        check_server_status.ServerState = MockedServerClass
        check_sequence.Cacti = Mock()
        with patch("server_deployment.nsone_class.Ns1Deploy.get_zone") \
                as ns1_mock:
            ns1_mock.return_value = NS1ZoneMock()
            self.testing_class = check_server_status.CheckingSequence(args)

        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_fw_rules(self, conn):
        connection = Mock()
        conn.return_value = connection
        connection.exec_command.return_value = [
            '1', MockedExecOutput([
                '22/tcp                     ALLOW       111.111.111.11',
            ], return_status=1), '3'
        ]
        self.testing_class.check_fw_rules()

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_fw_rules(self, conn):
        connection = Mock()
        conn.return_value = connection
        connection.exec_command.return_value = [
            '1', MockedExecOutput([
                '22/tcp                     ALLOW       111.111.111.11',
            ], return_status=0), '3'
        ]
        self.testing_class.check_fw_rules()
        connection.exec_command.assert_called_with(
            'sudo ufw status|grep 111.111.111.11'
        )

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_fw_rules_not_found(self, conn):
        connection = Mock()
        conn.return_value = connection
        connection.exec_command.return_value = [
            '1', MockedExecOutput([
                '',
            ], return_status=0), '3'
        ]
        self.testing_class.check_fw_rules()

        connection.exec_command.assert_called_with(
            'sudo ufw status|grep 111.111.111.11'
        )
        self.assertEquals(
            self.testing_class.check_status["check_fw_rules"],
            "Not OK"
        )

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_server_consistency(self, conn):
        connection = Mock()
        conn.return_value = connection
        self.testing_class.server = Mock()

        self.testing_class.check_server_consistency()
        self.assertEquals(
            self.testing_class.check_status["check_server_consistency"],
            "OK"
        )

        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_server_consistency_not_enouph_ram(self, conn):
        connection = Mock()
        conn.return_value = connection
        self.testing_class.server = Mock()
        self.testing_class.server.check_ram_size.side_effect = DeploymentError('RAM')
        self.testing_class.check_server_consistency()
        self.assertEquals(
            self.testing_class.check_status["check_server_consistency"],
            "Not OK"
        )
        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_server_consistency_not_enouph_space(self, conn):
        connection = Mock()
        conn.return_value = connection
        self.testing_class.server = Mock()
        self.testing_class.server.check_free_space.side_effect = DeploymentError('RAM')
        self.testing_class.check_server_consistency()
        self.assertEquals(
            self.testing_class.check_status["check_server_consistency"],
            "Not OK"
        )

        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_server_consistency_wrong_architecture(self, conn):
        connection = Mock()
        conn.return_value = connection
        self.testing_class.server = Mock()
        self.testing_class.server.check_hw_architecture.side_effect = DeploymentError('RAM')

        self.testing_class.check_server_consistency()
        self.assertEquals(
            self.testing_class.check_status["check_server_consistency"],
            "Not OK"
        )

        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_server_consistency_wrong_os(self, conn):
        connection = Mock()
        conn.return_value = connection
        self.testing_class.server = Mock()
        self.testing_class.server.check_os_version.side_effect = DeploymentError('RAM')

        self.testing_class.check_server_consistency()
        self.assertEquals(
            self.testing_class.check_status["check_server_consistency"],
            "Not OK"
        )

        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    @patch('check_server_status.CheckingSequence.connect_to_serv')
    def test_check_server_consistency_not_ping(self, conn):
        connection = Mock()
        conn.return_value = connection
        self.testing_class.server = Mock()
        self.testing_class.server.check_ping_8888.side_effect = DeploymentError('RAM')

        self.testing_class.check_server_consistency()
        self.assertEquals(
            self.testing_class.check_status["check_server_consistency"],
            "Not OK"
        )

        self.testing_class.server.check_ram_size.assert_called()
        self.testing_class.server.check_free_space.assert_called()
        self.testing_class.server.check_hw_architecture.assert_called()
        self.testing_class.server.check_os_version.assert_called()
        self.testing_class.server.check_ping_8888.assert_called()

    def test_check_hostname(self):
        self.testing_class.server = Mock()
        self.testing_class.server.check_hostname.return_value = "test-host.test.test"
        self.testing_class.check_hostname()
        self.assertEquals(
            self.testing_class.check_status["check_hostname"],
            "OK"
        )
        self.testing_class.server.check_hostname.assert_called()

    def test_check_hostname_wrong_name(self):
        self.testing_class.server = Mock()
        self.testing_class.server.check_hostname.return_value = "wrong_test-host.test.test"
        self.testing_class.check_hostname()
        self.assertEquals(
            self.testing_class.check_status["check_hostname"],
            "Not OK"
        )
        self.testing_class.server.check_hostname.assert_called()

    def test_check_ns1_a_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = {"record": "record"}
        self.testing_class.check_ns1_a_record()
        self.assertEquals(
            self.testing_class.check_status["check_ns1_a_record"],
            "OK"
        )
        self.testing_class.ns1.get_a_record.assert_called()

    def test_check_ns1_a_record_no_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = None
        self.testing_class.check_ns1_a_record()
        self.assertEquals(
            self.testing_class.check_status["check_ns1_a_record"],
            "Not OK"
        )
        self.testing_class.ns1.get_a_record.assert_called()

    def test_check_infradb(self):
        self.testing_class.infradb = Mock()
        self.testing_class.infradb.get_server.return_value = {"record": "record"}
        self.testing_class.check_infradb()
        self.assertEquals(
            self.testing_class.check_status["check_infradb"],
            "OK"
        )
        self.testing_class.infradb.get_server.assert_called()

    def test_check_infradb_no_record(self):
        self.testing_class.infradb = Mock()
        self.testing_class.infradb.get_server.return_value = None
        self.testing_class.check_infradb()
        self.assertEquals(
            self.testing_class.check_status["check_infradb"],
            "Not OK"
        )
        self.testing_class.infradb.get_server.assert_called()

    def test_check_cds(self):
        check_sequence.CDSAPI = Mock()
        check_sequence.CDSAPI.check_server_exist.return_value = {"record": "record"}
        self.testing_class.check_cds()
        self.assertEquals(
            self.testing_class.check_status["check_cds"],
            "OK"
        )

    def test_check_ns1_balancing_rule(self):
        record = NS1MockedRecord({
            "answers": [
                {'answer': ['111.111.111.11',]},
                {'answer': ['222.222.222.22',]},
                {'answer': ['333.333.333.33',]},
            ]
        })
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = record
        self.testing_class.check_ns1_balancing_rule()
        self.assertEquals(
            self.testing_class.check_status["check_ns1_balancing_rule"],
            "OK"
        )
        self.testing_class.ns1.get_a_record.assert_called()

    def test_check_ns1_balancing_rule_no_record(self):
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = None
        self.testing_class.check_ns1_balancing_rule()
        self.assertEquals(
            self.testing_class.check_status["check_ns1_balancing_rule"],
            "Not OK"
        )
        self.testing_class.ns1.get_a_record.assert_called()

    def test_check_ns1_balancing_rule_no_answer(self):
        record = NS1MockedRecord({
            "answers": [
                {'answer': ['222.222.222.22',]},
                {'answer': ['333.333.333.33',]},
            ]
        })
        self.testing_class.ns1 = Mock()
        self.testing_class.ns1.get_a_record.return_value = record
        self.testing_class.check_ns1_balancing_rule()
        self.assertEquals(
            self.testing_class.check_status["check_ns1_balancing_rule"],
            "Not OK"
        )
        self.testing_class.ns1.get_a_record.assert_called()

    def test_check_nagios(self):
        self.testing_class.nagios = Mock()
        self.testing_class.nagios.get_host.return_value = {"record": "record"}
        self.testing_class.nagios.check_services_status.return_value = False
        self.testing_class.check_nagios()
        self.assertEquals(
            self.testing_class.check_status["check_nagios"],
            "OK"
        )
        self.testing_class.nagios.get_host.assert_called()
        self.testing_class.nagios.check_services_status.assert_called()

    def test_check_nagios_no_host(self):
        self.testing_class.nagios = Mock()
        self.testing_class.nagios.get_host.return_value = None
        self.testing_class.nagios.check_services_status.return_value = True
        self.testing_class.check_nagios()
        self.assertEquals(
            self.testing_class.check_status["check_nagios"],
            "Not OK"
        )
        self.testing_class.nagios.get_host.assert_called()
        self.testing_class.nagios.check_services_status.assert_not_called()

    def test_check_nagios_no_host_exception(self):
        self.testing_class.nagios = Mock()
        self.testing_class.nagios.get_host.side_effect = Exception()
        self.testing_class.nagios.check_services_status.return_value = True
        self.testing_class.check_nagios()
        self.assertEquals(
            self.testing_class.check_status["check_nagios"],
            "Not OK"
        )
        self.testing_class.nagios.get_host.assert_called()
        self.testing_class.nagios.check_services_status.assert_not_called()

    def test_check_nagios_services_down(self):
        self.testing_class.nagios = Mock()
        self.testing_class.nagios.get_host.return_value = {"record": "record"}
        self.testing_class.nagios.check_services_status.side_effect = DeploymentError('error')
        self.testing_class.check_nagios()
        self.assertEquals(
            self.testing_class.check_status["check_nagios"],
            "Not OK"
        )
        self.testing_class.nagios.get_host.assert_called()
        self.testing_class.nagios.check_services_status.assert_called()

    def test_check_pssh_file(self):
        connection = Mock()
        self.testing_class.connect_to_serv = Mock(return_value=connection)
        connection.exec_command.return_value = [
            1, MockedExecOutput(['test_server', ]), 1
        ]
        self.testing_class.check_pssh_file()
        connection.exec_command.assert_called_with('grep "%s" %s' % (
            'test-host', settings.PSSH_FILE_PATH
        ))
        self.assertEquals(
            self.testing_class.check_status["check_pssh_file"],
            "OK"
        )

    def test_check_pssh_file_no_file(self):
        connection = Mock()
        self.testing_class.connect_to_serv = Mock(return_value=connection)
        connection.exec_command.return_value = [
            1, MockedExecOutput([ ]), 1
        ]
        self.testing_class.check_pssh_file()
        connection.exec_command.assert_called_once_with('grep "%s" %s' % (
            'test-host', settings.PSSH_FILE_PATH
        ))

        self.assertEquals(
            self.testing_class.check_status["check_pssh_file"],
            "Not OK"
        )

    @patch('check_server_status.CheckingSequence')
    def test_main_check_server_status(self, check_seq):
        # test for check that all of arguments is parsed
        check_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        check_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        check_sequence.argparse.ArgumentParser = mocked_args
        check_sequence.sys = Mock()
        check_sequence.main()
        test_data = [
            '--host_name', '--zone_name', '--IP', '--record_type',
            '--login', '--password', '--cert', '--hosting',
            '--server_group', '--environment', '--dns_balancing_name',
            '--first_step', '--number_of_steps_to_execute',
            '--disable_infradb_ssl'
        ]
        self.assertEqual(test_data, mocked_args.added_arguments)

    @patch('check_server_status.CheckingSequence')
    def test_main_check_server_status_required_list(self, check_seq):
        # test for check that all of arguments is parsed
        check_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        check_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        check_sequence.argparse.ArgumentParser = mocked_args
        check_sequence.sys = Mock()
        check_sequence.main()
        test_data = ['--host_name', '--IP']
        print mocked_args.required_arguments
        self.assertEqual(test_data, mocked_args.required_arguments)

    @patch('check_server_status.CheckingSequence')
    def test_main_check_server_status_default_values(self, check_seq):
        # test for check that all of arguments is parsed
        check_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        check_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        check_sequence.argparse.ArgumentParser = mocked_args
        check_sequence.sys = Mock()
        check_sequence.main()
        test_data = {
            '--record_type': 'A',
            '--server_group': '5588823fbde7a0d00338ce8d',
            '--login': 'robot',
            '--zone_name': 'attested.club',
            '--environment': 'prod',
            '--hosting': 'HE',
            '--first_step': 'check_server_consistency'
        }

        print mocked_args.default_values
        self.assertEqual(test_data, mocked_args.default_values)

    @patch('check_server_status.CheckingSequence')
    def test_main_check_server_status_step_choices(self, check_seq):
        # test for check that all of arguments is parsed
        check_sequence.argparse = Mock()
        mocked_args = MockedArgPars()
        check_sequence.argparse.ArgumentDefaultsHelpFormatter = mocked_args
        check_sequence.argparse.ArgumentParser = mocked_args
        check_sequence.sys = Mock()
        check_sequence.main()
        test_data = [
            'check_server_consistency', 'check_hostname', 'check_ns1_a_record',
            'check_infradb', 'check_cds', 'check_nagios', 'check_puppet',
            'check_ns1_balancing_rule', 'check_pssh_file', 'check_fw_rules',
            'check_cacti'
        ]

        print mocked_args.step_choices
        self.assertEqual(test_data, mocked_args.step_choices)

    def test_check_cacti(self):
        self.testing_class.cacti = Mock()
        self.testing_class.cacti.find_device.return_value = 1
        self.testing_class.cacti.find_graph.return_value = True

        self.testing_class.check_cacti()
        self.testing_class.cacti.find_device.assert_called()
        self.testing_class.cacti.find_graph.assert_called()
        self.assertEquals(
            self.testing_class.check_status["check_cacti"],
            "OK"
        )

    def test_check_cacti_no_host(self):
        self.testing_class.cacti = Mock()
        self.testing_class.cacti.find_device.return_value = None
        self.testing_class.cacti.find_graph.return_value = True
        self.testing_class.check_cacti()
        self.testing_class.cacti.find_device.assert_called()
        self.testing_class.cacti.find_graph.assert_not_called()
        self.assertEquals(
            self.testing_class.check_status["check_cacti"],
            "Not OK"
        )

    def test_check_cacti_no_graph(self):
        self.testing_class.cacti = Mock()
        self.testing_class.cacti.find_device.return_value = 1
        self.testing_class.cacti.find_graph.return_value = False
        self.testing_class.check_cacti()
        self.testing_class.cacti.find_device.assert_called()
        self.testing_class.cacti.find_graph.assert_called()
        self.assertEquals(
            self.testing_class.check_status["check_cacti"],
            "Not OK"
        )


class TestCacti(TestAbstract):
    @patch("settings.INFRADB_URL", 'http://localhost:8000/api/')
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

        self.logger = Mock()
        for handler in nagios_deploy.logger.handlers:
            if isinstance(handler, MongoDBHandler):
                handler.add_mongo_logger(self.logger)
        self.host_name = 'test-test1.host'
        self.short_host = 'test-test1'
        self.connection = Mock()
        cacti_deploy.paramiko = Mock()
        cacti_deploy.paramiko.SSHClient.connect.return_value = self.connection
        cacti_deploy.paramiko.RSAKey.from_private_key_file.return_value = 'key'
        self.testing_class = cacti_deploy.Cacti(
            self.host_name, self.logger, self.short_host
        )

        # print name of running test
        print("RUN_TEST %s" % self._testMethodName)

    def test_add_device(self):
        self.testing_class.client = Mock()
        self.testing_class.find_device = Mock(return_value=None)
        self.testing_class.find_host_template = Mock(return_value='1')
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', 'Success - new device-id: (12)'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.add_device()

        self.testing_class.find_device.assert_called()
        self.testing_class.find_host_template.assert_called()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_device.php --description=%s --ip=%s --community=%s --template=%s" % (
                'test-test1', 'test-test1.host', settings.CACTI_SNMP_COMMUNITY_NAME, 1
            )
        )
        self.assertEquals(result, '12')

    def test_add_device_already_exist(self):
        self.testing_class.client = Mock()
        self.testing_class.find_device = Mock(return_value='1')
        self.testing_class.find_host_template = Mock(return_value='1')
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', 'Success - new device-id: (12)'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.add_device()

        self.testing_class.find_device.assert_called()
        self.testing_class.find_host_template.assert_not_called()
        self.testing_class.client.exec_command.assert_not_called()
        self.assertEquals(result, '1')

    def test_add_device_error(self):
        self.testing_class.client = Mock()
        self.testing_class.find_device = Mock(return_value=None)
        self.testing_class.find_host_template = Mock(return_value='1')
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', 'Success - new device-id: (12)'],
                return_status=1
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_device
        )

        self.testing_class.find_device.assert_called()
        self.testing_class.find_host_template.assert_called()
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_device.php --description=%s --ip=%s --community=%s --template=%s" % (
                'test-test1', 'test-test1.host', settings.CACTI_SNMP_COMMUNITY_NAME, 1
            )
        )

    def test_find_host_template(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_host_template('test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_device.php --list-host-templates"
        )
        self.assertEquals(result, '1')

    def test_find_host_template_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_host_template,
            'test_name'
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_device.php --list-host-templates"
        )

    def test_find_device(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_device('test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-hosts"
        )
        self.assertEquals(result, '1')

    def test_find_device_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_device('test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-hosts"
        )
        self.assertEquals(result, None)

    def test_find_graph_template(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_graph_template('test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-graph-templates"
        )
        self.assertEquals(result, '1')

    def test_find_graph_template_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_graph_template,
            'test_name'
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-graph-templates"
        )

    def test_find_tree(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_tree('test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_tree.php --list-trees"
        )
        self.assertEquals(result, '1')

    def test_find_tree_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_tree,
            'test_name'
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_tree.php --list-trees"
        )

    def test_find_graph(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_graph(8, 'test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_perms.php --list-graphs --host-id=%s" % 8
        )
        self.assertEquals(result, '1')

    def test_find_graph_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_graph(8, 'test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_perms.php --list-graphs --host-id=%s" % 8
        )
        self.assertEquals(result, None)

    def test_find_value(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_value(8, 'test_name', 'find_value')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-values  --host-id=%s --snmp-field=%s" % (
                8, 'find_value'
            )
        )
        self.assertEquals(result, '1')

    def test_find_value_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_value,
            8, 'test_name', 'find_value'
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-values  --host-id=%s --snmp-field=%s" % (
                8, 'find_value'
            )
        )

    def find_snmp_querie(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_snmp_querie('test_name')
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-queries"
        )
        self.assertEquals(result, '1')

    def test_find_snmp_querie_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_snmp_querie,
            'test_name'
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-queries"
        )

    def test_find_snmp_querie_type(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\ttest_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.find_snmp_querie_type('test_name', 13)
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-query-types  --snmp-query-id=%s" % 13
        )
        self.assertEquals(result, '1')

    def test_find_snmp_querie_type_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['test_server', '1\twrong_name', '2\tother_name'],
                return_status=0
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.find_snmp_querie_type,
            'test_name', 13
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-query-types  --snmp-query-id=%s" % 13
        )

    def test_add_graph_to_tree(self):
        self.testing_class.client = Mock()
        self.testing_class.find_tree = Mock(return_value=8)
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['Added Node node-id: (9)    ',],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.add_graph_to_tree(15)
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_tree.php --type=node --node-type=graph --tree-id=%s --graph-id=%s" % (
                8, 15
            )
        )
        self.assertEquals(result, '9')

    def test_add_graph_to_tree_no_answer(self):
        self.testing_class.client = Mock()
        self.testing_class.find_tree = Mock(return_value=8)
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['Added Node node-id: (9)    ',],
                return_status=1
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_graph_to_tree,
            15
        )
        self.testing_class.client.exec_command.assert_called_with(
            "sudo php -q /usr/share/cacti/cli/add_tree.php --type=node --node-type=graph --tree-id=%s --graph-id=%s" % (
                8, 15
            )
        )

    def test_add_graph(self):
        self.testing_class.client = Mock()
        self.testing_class.find_graph_template = Mock(return_value=8)
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['Graph Added - graph-id: (9)    ',],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.add_graph('test_template', 15)
        self.testing_class.client.exec_command.assert_called_with(
            'sudo php -q /usr/share/cacti/cli/add_graphs.php --graph-type=%s --graph-template-id=%s --host-id=%s %s' % (
                "cg", 8, 15, ''
            )
        )
        self.assertEquals(result, '9')

    def test_add_graph_error(self):
        self.testing_class.client = Mock()
        self.testing_class.find_graph_template = Mock(return_value=8)
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['Graph Added - graph-id: (9)    ',],
                return_status=1
            ),
            1
        ]
        self.assertRaises(
            DeploymentError,
            self.testing_class.add_graph,
            'test_template', 15
        )
        self.testing_class.client.exec_command.assert_called_with(
            'sudo php -q /usr/share/cacti/cli/add_graphs.php --graph-type=%s --graph-template-id=%s --host-id=%s %s' % (
                "cg", 8, 15, ''
            )
        )

    def test_add_graph_traffic(self):
        self.testing_class.client = Mock()
        self.testing_class.find_graph_template = Mock(return_value=8)
        self.testing_class.find_snmp_querie = Mock(return_value=9)
        self.testing_class.find_snmp_querie_type = Mock(return_value=10)
        self.testing_class.find_value = Mock(return_value=11)
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['Graph Added - graph-id: (9)    ',],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.add_graph("Interface - Traffic (bits/sec)", 15)
        self.testing_class.client.exec_command.assert_called_with(
            'sudo php -q /usr/share/cacti/cli/add_graphs.php --graph-type=%s --graph-template-id=%s --host-id=%s %s' % (
                "ds", 8, 15, ' --snmp-query-id=9 --snmp-query-type-id=10 --snmp-field=ifIP --snmp-value=11'
            )
        )
        self.testing_class.find_graph_template.assert_called()
        self.testing_class.find_snmp_querie.assert_called()
        self.testing_class.find_snmp_querie_type.assert_called()
        self.testing_class.find_value.assert_called()
        self.assertEquals(result, '9')

    def test_add_graph_free_space(self):
        self.testing_class.client = Mock()
        self.testing_class.find_graph_template = Mock(return_value=8)
        self.testing_class.find_snmp_querie = Mock(return_value=9)
        self.testing_class.find_snmp_querie_type = Mock(return_value=10)
        self.testing_class.find_value = Mock(return_value=11)
        self.testing_class.client.exec_command.return_value = [
            1,
            MockedExecOutput(
                ['Graph Added - graph-id: (9)    ',],
                return_status=0
            ),
            1
        ]
        result = self.testing_class.add_graph('ucd/net - Available Disk Space', 15)
        self.testing_class.client.exec_command.assert_called_with(
            'sudo php -q /usr/share/cacti/cli/add_graphs.php --graph-type=%s --graph-template-id=%s --host-id=%s %s' % (
                "ds", 8, 15, ' --snmp-query-id=9 --snmp-query-type-id=10 --snmp-field=dskDevice --snmp-value=11'
            )
        )
        self.testing_class.find_graph_template.assert_called()
        self.testing_class.find_snmp_querie.assert_called()
        self.testing_class.find_snmp_querie_type.assert_called()
        self.testing_class.find_value.assert_called()
        self.assertEquals(result, '9')


if __name__ == '__main__':
    unittest.main()
