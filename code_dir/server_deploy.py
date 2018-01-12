
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


class DeploySequence(SequenceAbstract):

    def __init__(self, args):
        super(DeploySequence, self).__init__(args)

        self.steps = {
            "check_server_consistency": self.check_server_consistency,
            "check_hostname": self.check_hostname_step,
            "add_ns1_a_record": self.add_ns1_a_record,
            "add_to_infradb": self.add_to_infradb,
            "update_fw_rules": self.update_fw_rules,
            "install_puppet": self.install_puppet,
            "run_puppet": self.run_puppet,
            "add_to_cds": self.deploy_cds,
            "add_to_nagios": self.add_to_nagios,
            "add_ns1_monitor": self.add_ns1_monitor,
            "add_ns1_balancing_rule": self.add_ns1_balancing_rule,
            "add_to_pssh_file": self.add_to_pssh_file

        }
        self.step_sequence = [
            "check_server_consistency",
            "check_hostname",
            "add_ns1_a_record",
            "add_to_infradb",
            "update_fw_rules",
            "install_puppet",
            "run_puppet",
            "add_to_cds",
            "add_to_nagios",
            "add_ns1_monitor",
            "add_ns1_balancing_rule",
            "add_to_pssh_file",
        ]

        self.record_type = args.record_type
        # self.zone_name = "attested.club"
        self.server = ServerState(
            self.host_name, args.login, args.password,
            self.logger, ipv4=self.ip,
            first_step=self.first_step,
        )

    def deploy_cds(self):
        # checking installed packages
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        cds.check_installed_packages(self.server)

        cds_server = cds.check_server_exist()
        if cds_server:
            group_added = cds.check_server_in_group()
            check_list = cds.check_need_update_versions()
        else:
            group_added = False
            check_list = {
                'ssl': True,
                'waf_sdk': True,
                'domain_purge': True
            }
            cds.add_server(args.IP, args.environment)
        if check_list['ssl']:
            cds.monitor_ssl_configuration()
        if check_list['waf_sdk']:
            cds.update_server(
                {
                    "app_config_version": 0,
                    "waf_rule_version": 0
                }
            )
            cds.monitor_waf_and_sdk_configuration()
        if check_list['domain_purge']:
            cds.update_server(
                {
                    "domain_config_version": 0,
                    "purge_version": 0,
                }
            )
        if not group_added:
            cds.add_server_to_group()
        if check_list['domain_purge']:
            cds.monitor_purge_and_domain_configuration()
        self.group = cds.server_group
        logger.info("Reboot server to apply  changes")
        self.server.reboot()
        time.sleep(settings.CDS_WAITING_TIME)

    def update_fw_rules(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=settings.INSTALL_SERVER_HOST,
            username=settings.INSTALL_SERVER_LOGIN,
            password=settings.INSTALL_SERVER_PASSWORD,
            port=22
        )
        logger.info("sudo bash /opt/revsw-firewall-manager/update_all.sh")
        stdin_fw, stdout_fw, stderr_fw = client.exec_command(
            "sudo bash /opt/revsw-firewall-manager/update_all.sh"
        )
        lines = stdout_fw.readlines()
        for line in lines:
            logger.info(line)
        if stdout_fw.channel.recv_exit_status() != 0:
            log_error = "Problem with FW rules update on INSTALL server"
            self.logger.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)
        logger.info("sudo puppet agent -t")
        stdin_pu, stdout_pu, stderr_pu = client.exec_command(
            "sudo puppet agent -t"
        )
        lines = stdout_pu.readlines()
        for line in lines:
            logger.info(line)
        # if stdout_pu.channel.recv_exit_status() != 0:
        #     log_error = "Problem with puppet agent on INSTALL server"
        #     self.logger.log({"fw": "fail", "log": log_error}, "puppet")
        #     raise DeploymentError(log_error)
        client.close()

    def sign_ssl_puppet(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=settings.INSTALL_SERVER_HOST,
            username=settings.INSTALL_SERVER_LOGIN,
            password=settings.INSTALL_SERVER_PASSWORD,
            port=22
        )
        logger.info("sudo puppet cert sign %s" % self.host_name)
        stdin_fw, stdout_fw, stderr_fw = client.exec_command(
            "sudo puppet cert sign %s" % self.host_name
        )
        lines = stdout_fw.readlines()
        for line in lines:
            logger.info(line)
        if stdout_fw.channel.recv_exit_status() != 0:
            log_error = "Problem with sudo puppet cert sign %s" % \
                        self.host_name
            self.logger.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)
        client.close()

    def check_hostname_step(self):
        # Start deploing of server
        hostname = self.server.check_hostname()
        if hostname.rstrip() != self.host_name:
            self.server.update_hostname(self.host_name)
            # Reboot server to update hostname
            logger.info("Reboot new server")
            self.server.reboot()

    def add_to_infradb(self):
        server_versions = {
            "proxy_software_version": 1,
            "kernel_version": 1,
            "revsw_module_version": 1,
        }
        server = self.infradb.get_server(self.host_name)
        if server:
            logger.info("Server already added to infradb")
            return
        self.infradb.add_server(
            self.host_name, self.ip, server_versions,
        )

    def install_puppet(self):
        self.server.remove_puppet()
        self.remove_from_puppet()
        self.server.install_puppet()
        self.server.configure_puppet()

    def run_puppet(self):
        logger.info("Run puppet")
        first_run = self.server.run_puppet()
        if first_run != 0:
            self.sign_ssl_puppet()
            self.server.run_puppet()

    def add_to_nagios(self):
        # NAGIOS configurate
        logger.info("Configure nagios")
        nagios_data = {
            'host_name': self.short_name,
            "ip": self.ip,
            "location_code": self.location_code
        }
        self.nagios.create_config_file(nagios_data)
        self.nagios.send_config_to_server()
        if self.nagios.check_nagios_config() != 0:
            raise DeploymentError('nagios config is not ok')
        self.nagios.reload_nagios()

    def add_ns1_a_record(self):
        logger.info("Add NS1 A record")

        record = self.ns1.get_a_record(
            self.zone, self.short_name, self.record_type
        )
        if record:
            if record.data['answers'][0]['answer'][0] != [self.ip,]:
                raise DeploymentError('Record already exist but with other IP')
            logger.info(' A record already exist with id %s' % record['id'])
            return
        record = self.ns1.add_a_record(self.zone, self.short_name)
        logger.info("A NS1 record id %s" % record['id'])

    def add_ns1_monitor(self):
        # Add server to NS1
        logger.info("Start server adding to NS1")
        logger.info('Cheking  monitors list if server already have monitor')
        monitor_id = self.ns1.check_is_monitor_exist()
        if not monitor_id:
            monitor_id = self.ns1.add_new_monitor()
            logger.info("New monitor id %s" % monitor_id)
            logger.info(
                "Waiting for %s seconds  to new monitor is setting" % settings.NS1_WAITING_TIME
            )
            time.sleep(settings.NS1_WAITING_TIME)
        else:
            logger.info("monitor already exist with id %s" % monitor_id)
        monitor_status = self.ns1.check_monitor_status(monitor_id)
        if monitor_status != 'up':
            raise DeploymentError("New monitor not in UP status")
        logger.info("New monitor is UP")
        feed_id = self.ns1.find_feed(settings.NS1_DATA_SOURCE_ID, monitor_id)
        if not feed_id:
            self.ns1.add_feed(settings.NS1_DATA_SOURCE_ID, monitor_id)

    def add_ns1_balancing_rule(self):
        logger.info("Checking nagios services")
        self.nagios.check_services_status()

        monitor_id = self.ns1.check_is_monitor_exist()
        if not monitor_id:
            raise DeploymentError("Monitor not exist")
        monitor_status = self.ns1.check_monitor_status(monitor_id)
        if monitor_status != 'up':
            raise DeploymentError("Monitor not in UP status")
        feed_id = self.ns1.find_feed(settings.NS1_DATA_SOURCE_ID, monitor_id)
        if not feed_id:
            raise DeploymentError("Data feed for moniton %s not found" % monitor_id)
        logger.info("Add server %s answer to NS1 to record %s" % (
            self.ip, self.dns_balancing_name
        ))
        self.ns1.add_answer(
            self.balancing_rule_zone, self.dns_balancing_name, self.record_type,
            self.ip, self.location_code, feed_id
        )

    def check_server_consistency(self):
        self.server.check_ram_size()
        self.server.check_free_space()
        self.server.check_hw_architecture()
        self.server.check_os_version()
        self.server.check_ping_8888()

    def add_to_pssh_file(self):
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
            logger.info("Server already added")
            return
        logger.info("adding server to %s" % settings.PSSH_FILE_PATH)
        client.exec_command("sudo echo %s >> %s" % (
            self.short_name, settings.PSSH_FILE_PATH
        ))


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
            "add_ns1_a_record",
            "add_to_infradb",
            "update_fw_rules",
            "install_puppet",
            "run_puppet",
            "add_to_cds",
            "add_to_nagios",
            "add_ns1_monitor",
            "add_ns1_balancing_rule",
            "add_to_pssh_file",
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
        sequence = DeploySequence(args)
        sequence.run_sequence()

    except DeploymentError as e:
        logger.critical(e.message)
        logger.error(e, exc_info=True)
        sys.exit(-1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(-1)
