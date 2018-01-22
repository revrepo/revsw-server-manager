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
import logging
import logging.config

import sys

import re

import settings
from server_deployment.abstract_sequence import SequenceAbstract

from server_deployment.cds_api import CDSAPI

from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError


logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class CheckingSequence(SequenceAbstract):
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

            "check_server_consistency": {
                "type": "object",
                "properties": {
                    "runned": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "check_ram_size": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "check_free_space": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "check_hw_architecture": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "check_os_version": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "check_ping_8888": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_hostname": {
                "type": "object",
                "properties": {
                    "runned": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "check_hostname": {
                        "type": "string", "pattern": "yes|no|fail"
                    },
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_ns1_a_record": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_infradb": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_cds": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_nagios": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_puppet": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_ns1_balancing_rule": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_pssh_file": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
            "check_fw_rules": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}
                },
            },
        },
        "required": [
            "time",
            "start_time",
            "initial_data",
            "init_step",
            "check_server_consistency",
            "check_hostname",
            "check_ns1_a_record",
            "check_infradb",
            "check_cds",
            "check_nagios",
            "check_puppet",
            "check_ns1_balancing_rule",
            "check_pssh_file",
            "check_fw_rules",
        ]
    }
    logger_steps = [
        "init_step",
        "check_server_consistency",
        "check_hostname",
        "check_ns1_a_record",
        "check_infradb",
        "check_cds",
        "check_nagios",
        "check_puppet",
        "check_ns1_balancing_rule",
        "check_pssh_file",
        "check_fw_rules",
    ]
    current_server_state = {
        "time": None,
        "init_step": {
            "runned": "no",
        },
        "check_server_consistency": {
            "runned": "no",
        },
        "check_hostname": {
            "runned": "no",
        },
        "check_ns1_a_record": {
            "runned": "no",
        },
        "check_infradb": {
            "runned": "no",
        },
        "check_cds": {
            "runned": "no",
        },
        "check_nagios": {
            "runned": "no",
        },
        "check_puppet": {
            "runned": "no",
        },
        "check_ns1_balancing_rule": {
            "runned": "no",
        },
        "check_pssh_file": {
            "runned": "no",
        },
        "check_fw_rules": {
            "runned": "no",
        },
    }

    check_status = {
        "server_consistency": 'Not checked',
        "check_hostname": 'Not checked',
        "check_ns1_a_record": "Not checked",
        "check_infradb": "Not checked",
        "check_cds": "Not checked",
        "check_nagios": "Not checked",
        "check_puppet": "Not checked",
        "check_ns1_balancing_rule": "Not checked",
        "check_pssh_file": "Not checked",
        "check_fw_rules": "Not checked",

    }

    def __init__(self, args):
        super(CheckingSequence, self).__init__(args)

        self.steps = {
            "check_server_consistency": self.check_server_consistency,
            "check_hostname": self.check_hostname,
            "check_ns1_a_record": self.check_ns1_a_record,
            "check_infradb": self.check_infradb,
            "check_cds": self.check_cds,
            "check_nagios": self.check_nagios,
            "check_puppet": self.check_puppet,
            "check_ns1_balancing_rule": self.check_ns1_balancing_rule,
            "check_pssh_file": self.check_pssh_file,
            "check_fw_rules": self.check_fw_rules,

        }
        self.step_sequence = [
            "check_server_consistency",
            "check_hostname",
            "check_ns1_a_record",
            "check_infradb",
            "check_cds",
            "check_nagios",
            "check_puppet",
            "check_ns1_balancing_rule",
            "check_pssh_file",
            "check_fw_rules",
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
        self.logger.init_new_step("check_server_consistency")
        checking = True
        checking_dict = {
            "check_ram_size": self.server.check_ram_size,
            "check_free_space": self.server.check_free_space,
            "check_hw_architecture": self.server.check_hw_architecture,
            "check_os_version": self.server.check_os_version,
            "check_ping_8888": self.server.check_ping_8888,
        }
        for check_name, check_func in checking_dict.iteritems():
            try:
                check_func()
                self.logger.log({check_name: "yes"})
            except DeploymentError as e:
                checking = False
                self.logger.log({check_name: "fail"})
                logger.info(e.message)
        if not checking:
            self.check_status["server_consistency"] = "Not OK"
        else:
            self.check_status["server_consistency"] = "OK"

    def check_hostname(self):
        self.logger.init_new_step("check_hostname")
        hostname = self.server.check_hostname()
        if hostname.rstrip() != self.host_name:
            self.logger.log({"check_hostname": "fail"})
            self.check_status["check_hostname"] = "Not OK"
            return
        self.logger.log({"check_hostname": "yes"})
        self.check_status["check_hostname"] = "OK"

    def check_ns1_a_record(self):
        self.logger.init_new_step("check_ns1_a_record")
        record = self.ns1.get_a_record(
            self.zone, self.short_name, self.record_type
        )
        if record:
            self.check_status["check_ns1_a_record"] = "OK"
            return
        self.check_status["check_ns1_a_record"] = "Not OK"

    def check_infradb(self):
        self.logger.init_new_step("check_infradb")
        server = self.infradb.get_server(self.host_name)
        if server:
            self.check_status["check_infradb"] = "OK"
            return
        self.check_status["check_infradb"] = "Not OK"

    def check_cds(self):
        self.logger.init_new_step("check_cds")
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        server = cds.check_server_exist()
        if server:
            self.check_status["check_cds"] = "OK"
            return
        self.check_status["check_cds"] = "Not OK"

    def check_ns1_balancing_rule(self):
        self.logger.init_new_step("check_ns1_balancing_rule")
        record = self.ns1.get_a_record(
            self.balancing_rule_zone, self.dns_balancing_name, self.record_type
        )
        if not record:
            logger.info(' A dns balance record not found')
            self.check_status["check_ns1_balancing_rule"] = "Not OK"
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
        self.logger.init_new_step("check_pssh_file")
        client = self.connect_to_serv(
            settings.PSSH_SERVER,
            settings.PSSH_SERVER_LOGIN,
            settings.PSSH_SERVER_PASSWORD
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

    def check_nagios(self):
        self.logger.init_new_step("check_nagios")
        logger.info("Check if server added to nagios")
        host = self.nagios.get_host()
        if not host:
            logger.info("Host not founded in Nagios")
            self.check_status["check_nagios"] = "Not OK"
            return
        logger.info("Checking nagios services")
        try:
            self.nagios.check_services_status()
        except DeploymentError as e:
            logger.info(e.message)
            self.check_status["check_nagios"] = "Not OK"
            return
        self.check_status["check_nagios"] = "OK"

    def check_puppet(self):
        self.logger.init_new_step("check_puppet")
        try:
            cds = CDSAPI(self.server_group, self.host_name, self.logger)
            cds.check_installed_packages(self.server)
        except DeploymentError:
            self.check_status["check_puppet"] = "Not OK"
            return
        self.check_status["check_puppet"] = "OK"

    def check_fw_rules(self):
        self.logger.init_new_step("check_fw_rules")
        client = self.connect_to_serv(
            settings.INSTALL_SERVER_HOST,
            settings.INSTALL_SERVER_LOGIN,
            settings.INSTALL_SERVER_PASSWORD
        )
        logger.info('sudo ufw status|grep %s' % self.ip)
        stdin_fw, stdout_fw, stderr_fw = client.exec_command(
            'sudo ufw status|grep %s' % self.ip
        )
        lines = stdout_fw.readlines()
        ip_founded = False
        for line in lines:
            m = re.search('ALLOW\s*(.+?)$', line)
            if m and m.group(1) == self.ip:
                ip_founded = True
            logger.info(line)
        if not ip_founded:
            raise DeploymentError("IP not founded in Fire wall rules")


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
            "check_nagios",
            "check_puppet",
            "check_ns1_balancing_rule",
            "check_pssh_file",
            "check_fw_rules",
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
