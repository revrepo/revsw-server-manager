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
import argparse
import time
import datetime
import logging
import logging.config

import paramiko
import sys

import re

import settings
from server_deployment.abstract_sequence import SequenceAbstract
from server_deployment.nagios_class import NagiosServer
from server_deployment.cds_api import CDSAPI
from server_deployment.infradb import InfraDBAPI

from server_deployment.mongo_logger import MongoLogger
from server_deployment.nsone_class import Ns1Deploy
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError


logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class CheckingSequence(SequenceAbstract):

    check_status = {
        "server_consistency": 'Not checked',
        "check_hostname": 'Not checked',
        "check_ns1_a_record": "Not checked",
        "check_infradb": "Not checked",
        "check_cds": "Not checked",
        "check_ns1_balancing_rule": "Not checked",
        "check_pssh_file": "Not checked",

    }

    def __init__(self, args):
        super(CheckingSequence, self).__init__(args)

        self.steps = {
            "check_server_consistency": self.check_server_consistency,
            "check_hostname": self.check_hostname,
            "check_ns1_a_record": self.check_ns1_a_record,
            "check_infradb": self.check_infradb,
            "check_cds": self.check_cds,
            "check_ns1_balancing_rule": self.check_ns1_balancing_rule,
            "check_pssh_file": self.check_pssh_file,

        }
        self.step_sequence = [
            "check_server_consistency",
            "check_hostname",
            "check_ns1_a_record",
            "check_infradb",
            "check_cds",
            "check_ns1_balancing_rule",
            "check_pssh_file"
        ]

        self.record_type = args.record_type
        # self.zone_name = "attested.club"
        self.hosting_name = args.hosting
        self.server = ServerState(
            self.host_name, args.login, args.password,
            self.logger, ipv4=self.ip,
            first_step=self.first_step,
        )

    def check_server_consistency(self):
        try:
            self.server.check_ram_size()
            self.server.check_free_space()
            self.server.check_hw_architecture()
            self.server.check_os_version()
            self.server.check_ping_8888()
        except DeploymentError as e:
            logger.info(e.message)
            self.check_status["server_consistency"] = "Not OK"
            return
        self.check_status["server_consistency"] = "OK"

    def check_hostname(self):
        hostname = self.server.check_hostname()
        if hostname.rstrip() != self.host_name:
            self.check_status["check_hostname"] = "Not OK"
            return
        self.check_status["check_hostname"] = "OK"

    def check_ns1_a_record(self):
        record = self.ns1.get_a_record(
            self.zone, self.short_name, self.record_type
        )
        if record:
            self.check_status["check_ns1_a_record"] = "OK"
            return
        self.check_status["check_ns1_a_record"] = "Not OK"

    def check_infradb(self):
        server = self.infradb.get_server(self.host_name)
        if server:
            self.check_status["check_infradb"] = "OK"
            return
        self.check_status["check_infradb"] = "Not OK"

    def check_cds(self):
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        server = cds.check_server_exist()
        if server:
            self.check_status["check_cds"] = "OK"
            return
        self.check_status["check_cds"] = "Not OK"

    def check_ns1_balancing_rule(self):
        record = self.ns1.get_a_record(
            self.balancing_rule_zone, self.dns_balancing_name, self.record_type
        )
        if not record:
            logger.info(' A dns balance record not found')
            return

        answer_exist = False
        for answer in record.data['answers']:
            if answer['answer'] == [self.ip]:
                answer_exist = True
        if answer_exist:
            self.check_status["check_ns1_balancing_rule"] = "OK"
            return
        self.check_status["check_ns1_balancing_rule"] = "Not OK"

    def check_pssh_file(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=settings.PSSH_SERVER,
            username=settings.PSSH_SERVER_LOGIN,
            password=settings.PSSH_SERVER_PASSWORD,
            port=22
        )
        logger.info("Check if server already added")
        (stdin, stdout, stderr) = client.exec_command('grep "%s" %s' % (
            self.short_name, settings.PSSH_FILE_PATH
        ))
        founded_lines = []
        lines = stdout.readlines()
        for line in lines:
            founded_lines.append(line)
        if founded_lines:
            self.check_status["check_pssh_file"] = "OK"
            return
        self.check_status["check_pssh_file"] = "Not OK"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Automatic deployment of server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-n", "--host_name", help="Host name of server",
        required=True
    )
    parser.add_argument(
        "-z", "--zone_name", help="Name of zone on NS1.",
        default=settings.NS1_DNS_ZONE_DEFAULT
    )
    parser.add_argument(
        "-i", "--IP", help="IP of server.", required=True
    )
    parser.add_argument(
        "-r", "--record_type", help="Type of record at NS1.",
        default="A"
    )
    parser.add_argument(
        "-l", "--login", help="Login of the server.",
        default="robot"
    )
    parser.add_argument(
        "-p", "--password", help="Password of the server.",
        default=''
    )
    parser.add_argument(
        "-c", "--cert", help="Certificate of the server."
    )
    parser.add_argument(
        "--hosting", help="Name of server hosting provider.",
        default="HE"
    )
    parser.add_argument(
        "--server_group", help="CDS group.",
        default=settings.SERVER_GROUP
    )
    parser.add_argument(
        "--environment", help="Environment of server.",
        default='prod'
    )
    parser.add_argument(
        "--dns_balancing_name", help="DNS global load balancing name."
    )

    parser.add_argument(
        "--first_step", help="First step which sequence must start.",
        default="check_server_consistency",
        choices=[
            "check_server_consistency",
            "check_hostname",
            "check_ns1_a_record",
            "check_infradb",
            "check_cds",
            "check_ns1_balancing_rule",
            "check_pssh_file",
        ]
    )
    parser.add_argument(
        "--number_of_steps_to_execute",
        help="Number of steps need to be execute.",
        type=int,
    )

    parser.add_argument(
        "--disable_infradb_ssl", help="Disable ssl check  for infradb.",
        type=bool
    )
    args = parser.parse_args()

    try:
        sequence = CheckingSequence(args)
        sequence.run_sequence()
        logger.info(sequence.check_status)

    except DeploymentError as e:
        logger.critical(e.message)
        logger.error(e, exc_info=True)
        sys.exit(-1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(-1)
