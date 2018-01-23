
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
import logging.config
import datetime

import paramiko
import re

import settings
from server_deployment.infradb import InfraDBAPI
from server_deployment.mongo_logger import MongoLogger
from server_deployment.nagios_class import NagiosServer
from server_deployment.nsone_class import Ns1Deploy

from server_deployment.cds_api import CDSAPI
from server_deployment.utilites import DeploymentError, MongoDBHandler

# logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class SequenceAbstract(object):
    check_status = {}
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
            "init_step": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                }
            },
        },
        "required": ['time', "start_time", "initial_data", 'init_step']
    }
    current_server_state = {
        "time": None,
        "init_step": {
            "runned": "no",
        },
    }
    logger_steps = [
        "init_step",
    ]

    def __init__(self, args):

        # required aruments is host_name, ip,
        # first_step, number_of_steps, login, pasword, disable_infradb_ssl

        self.steps = {}  # dict for associate name of step and method
        self.step_sequence = []  # list of steps
        self.host_name = args.host_name
        self.short_name = self.get_short_name()
        self.ip = args.IP
        self.first_step = args.first_step
        if args.number_of_steps_to_execute:
            self.number_of_steps = args.number_of_steps_to_execute
        else:
            self.number_of_steps = None

        self.logger = MongoLogger(
            self.host_name, datetime.datetime.now().isoformat(),
            {
                "hostname": self.host_name,
                "ip": self.ip,
                "login": args.login,
                "password": args.password,
            },
            self.logger_schema,
            self.current_server_state,
            self.logger_steps
        )
        # adding MongoDb logger to logger handler
        for handler in logger.handlers:
            if isinstance(handler, MongoDBHandler):
                handler.add_mongo_logger(self.logger)
        self.logger.init_new_step('init_step')
        self.location_code = self.get_location_code()
        self.zone_name = self.get_zone_name(self.host_name)
        self.hosting_name = args.hosting
        # self.zone_name = "attested.club"

        self.ns1 = Ns1Deploy(self.host_name, self.ip, self.logger)
        self.server_group = args.server_group
        self.dns_balancing_name = args.dns_balancing_name
        # self.dns_balancing_name = "attested.club"
        if not self.dns_balancing_name:
            cds = CDSAPI(self.server_group, self.host_name, self.logger)
            self.dns_balancing_name = cds.server_group['edge_host']
        self.balancing_rule_zone = self.ns1.get_zone(
            self.get_zone_name(self.dns_balancing_name)
        )
        # self.balancing_rule_zone = self.ns1.get_zone(
        #     self.dns_balancing_name
        # )
        self.zone = self.ns1.get_zone(self.zone_name)
        self.infradb = InfraDBAPI(
            self.logger,
            self.location_code, self.hosting_name,
            ssl_disable=args.disable_infradb_ssl
        )
        self.nagios = NagiosServer(
            self.host_name, self.logger, self.short_name
        )

    def get_short_name(self):
        m = re.search('^(.+?)\.', self.host_name)
        if m:
            return m.group(1)
        raise DeploymentError("Wrong Host_name")

    def get_zone_name(self, name):
        m = re.search('^[-a-zA-Z0-9_]*\.(.+?)$', name)
        if m and m.group(1):
            return m.group(1)
        raise DeploymentError("Wrong Host_name")

    def remove_from_puppet(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=settings.INSTALL_SERVER_HOST,
            username=settings.INSTALL_SERVER_LOGIN,
            password=settings.INSTALL_SERVER_PASSWORD,
            port=22
        )
        logger.info("Deleting server %s from puppet" % self.host_name)
        logger.info("sudo puppet cert clean %s" % self.host_name)
        stdin_fw, stdout_fw, stderr_fw = client.exec_command(
            "sudo puppet cert clean %s" % self.host_name
        )
        lines = stdout_fw.readlines()
        for line in lines:
            logger.info(line)

        logger.info(
            "command sudo puppet cert clean %s"
            " was executed with status %s" % (
                self.host_name, stdout_fw.channel.recv_exit_status()
            )
            )
        logger.info("Server %s was deleted from puppet" % self.host_name)
        return stdout_fw.channel.recv_exit_status()

    def run_sequence(self):
        if self.first_step not in self.step_sequence:
            raise DeploymentError("Wrong first step")
        first_index = self.step_sequence.index(self.first_step)
        if not self.number_of_steps:
            self.number_of_steps = len(self.step_sequence)
        end_of_sequence = first_index + self.number_of_steps
        sequence_list = self.step_sequence[first_index:end_of_sequence]
        for step in sequence_list:
            if not step:
                break
            logger.info("=============== BEGIN %s STAGE ==============" % step)
            self.steps[step]()
            logger.info("=============== END %s STAGE ================" % step)
            if self.check_status:
                logger.info("Current Status of server %s" % self.check_status)

    def get_location_code(self):
        m = re.search('^(.+?)-', self.host_name)
        if m:
            return m.group(1)
        raise DeploymentError("Wrong Host_name")

    def connect_to_serv(self, hostname, login, password):

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=hostname,
            username=login,
            password=password,
            port=22
        )
        return client
