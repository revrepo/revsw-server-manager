
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
import datetime
import logging
import logging.config

import paramiko
import pymongo
import sys

import re

import settings
from server_deployment.nagios import Nagios
from server_deployment.cds_api import CDSAPI
from server_deployment.infradb import InfraDBAPI

from server_deployment.mongo_logger import MongoLogger
from server_deployment.nsone_class import NsOneDeploy
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)

class DeploySequence():


    def __init__(self, args):


        self.steps = {
            "check_hostname": self.check_hostname_step,
            "add_ns1_record": self.add_ns1_record,
            "add_to_infradb": self.add_to_infradb,
            "update_fw_rules": self.update_fw_rules,
            "install_puppet": self.install_puppet,
            "run_puppet": self.run_puppet,
            "add_to_cds": self.deploy_cds,
            "add_to_nagios": self.add_to_nagios,
            "add_ns1_monitor": self.add_ns1_monitor,
            "add_ns1_balancing_rule": self.add_ns1_balancing_rule,

        }
        self.step_sequence = [
            "check_hostname",
            "add_ns1_record",
            "add_to_infradb",
            "update_fw_rules",
            "install_puppet",
            "run_puppet",
            "add_to_cds",
            "add_to_nagios",
            "add_ns1_monitor",
            "add_ns1_balancing_rule",
        ]
        self.host_name = args.host_name
        self.server_group = args.server_group
        self.ip = args.IP
        self.first_step = args.first_step
        self.number_of_steps = args.number_of_steps_to_execute
        self.dns_balancing_name = args.dns_balancing_name
        self.zone_name = args.zone_name
        self.record_type = args.record_type

        self.logger = MongoLogger(self.host_name, datetime.datetime.now().isoformat())
        self.server = ServerState(
            self.host_name, args.login, args.password,
           self.logger, ipv4=self.ip, cert=args.cert
        )
        self.nsone = NsOneDeploy(self.host_name, self.host_name,self.logger)
        self.zone = self.nsone.get_zone(self.zone_name)
        self.infradb = InfraDBAPI(self.logger, ssl_disable=args.disable_infradb_ssl)


        self.location_code = self.get_location_code()

    def run_sequence(self):
        if self.first_step not in self.step_sequence:
            raise DeploymentError("Wrong first step")
        first_index = self.step_sequence.index(self.first_step)
        end_of_sequence = first_index + self.number_of_steps
        sequence_list = self.step_sequence[first_index:end_of_sequence]
        for step in sequence_list:
            logger.info("Running step %s" % step)
            self.steps[step]()

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

    def update_fw_rules(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=settings.INSTALL_SERVER_HOST,
            username=settings.INSTALL_SERVER_LOGIN,
            password=settings.INSTALL_SERVER_PASSWORD,
            port=22
        )
        logger.info("sudo sh /opt/revsw-firewall-manager/update_all.sh")
        stdin_fw, stdout_fw, stderr_fw = client.exec_command("sudo sh /opt/revsw-firewall-manager/update_all.sh")
        lines = stdout_fw.readlines()
        for line in lines:
            logger.info(line)
        if stdout_fw.channel.recv_exit_status() != 0:
            log_error = "Problem with FW rules update on INSTALL server"
            self.logger.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)
        logger.info("sudo puppet agent -t")
        stdin_pu, stdout_pu, stderr_pu = client.exec_command("sudo puppet agent -t")
        lines = stdout_pu.readlines()
        for line in lines:
            logger.info(line)
        if stdout_pu.channel.recv_exit_status() != 0:
            log_error = "Problem with pupprt agent on INSTALL server"
            self.logger.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)
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
            log_error = "Problem with sudo puppet cert sign %s" % self.host_name
            self.logger.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)
        client.close()

    def get_location_code(self):
        m = re.search('^(.+?)-', self.host_name)
        if m:
            return m.group(1)
        raise DeploymentError("Wrong Host_name")

    def remove_server_from_cds(self):
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        cds.update_server({"status": "offline"})
        cds.delete_server_from_groups()
        cds.delete_server()

    def check_hostname_step(self):
        # Start deploing of server
        logger.info("Checkin hostname")
        self.server.check_hostname()

        # Reboot server to update hostname
        logger.info("Reboot new server")
        self.server.reboot()

    def add_to_infradb(self):
        server_versions = {
            "proxy_software_version": 1,
            "kernel_version": 1,
            "revsw_module_version": 1,
        }
        logger.info("Adding server to inradb")
        self.infradb.add_server(
            self.host_name, self.ip, server_versions, self.location_code, self.host_name
        )

    def install_puppet(self):
        logger.info("Install  puppet")
        self.server.install_puppet()
        self.server.configure_puppet()

    def run_puppet(self):
        logger.info("Run puppet")
        self.server.run_puppet()
        self.sign_ssl_puppet()
        self.server.run_puppet()

    def add_to_nagios(self):
        # NAGIOS configurate
        logger.info("Configure nagios")
        nagios = Nagios(self.host_name,self.logger)
        nagios_data = {
            'host_name': self.host_name,
            "ip": self.ip,
            "location_code": self.location_code
        }
        nagios.create_config_file(nagios_data)
        nagios.send_config_to_server()
        nagios.reload_nagios()

    def add_ns1_record(self):
        logger.info("Add NS1 record")
        record = self.nsone.add_record(self.zone)
        logger.info("NS1 record id %s" % record['id'])
        record = self.nsone.get_record(self.zone, self.zone_name, self.record_type)

    def add_ns1_monitor(self):
        # Add server to NS1
        logger.info("Start server adding to NS1")

        monitor_id = self.nsone.add_new_monitor()
        logger.info("New monitor id %s" % monitor_id)
        self.nsone.add_feed(settings.NS1_DATA_SOURCE_ID)

    def add_ns1_balancing_rule(self):
        dns_balance_name = self.dns_balancing_name
        if not dns_balance_name:
            cds = CDSAPI(self.server_group, self.host_name, self.logger)
            dns_balance_name = cds.server_group['edge_host']
        logger.info("Add server %s answer to NS1 to record %s" % (self.ip, dns_balance_name))
        self.nsone.add_answer(self.zone, dns_balance_name, self.record_type, self.ip)
        # self.nsone.add_answer(self.zone, "test-alexus.attested.club", self.record_type, self.ip)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Automatic deployment of server.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--host_name", help="Host name of server", required=True)
    parser.add_argument("-z", "--zone_name", help="Name of zone on NSONE.", default="attested.club")
    parser.add_argument("-i", "--IP", help="IP of server.", required=True)
    parser.add_argument("-r", "--record_type", help="Type of record at NSONE.", default="A")
    parser.add_argument("-l", "--login", help="Login of the server.", default="robot")
    parser.add_argument("-p", "--password", help="Password of the server.", default='')
    parser.add_argument("-c", "--cert", help="Certificate of the server.")
    parser.add_argument(
        "--hosting", help="Name of server hosting provider.", default="HE Fremont 2 Facility"
    )
    parser.add_argument(
        "--server_group", help="CDS group.", default=settings.SERVER_GROUP
    )
    parser.add_argument(
        "--environment", help="Environment of server.", default='prod'
    )
    parser.add_argument(
        "--dns_balancing_name", help="DNS global load balancing name."
    )

    parser.add_argument(
        "--first_step", help="First step which sequence must start.", default='check_hostname'
    )
    parser.add_argument(
        "--number_of_steps_to_execute",
        help="Number of steps need to be execute.",
        default=10,
        type = int,
    )

    parser.add_argument(
        "--disable_infradb_ssl", help="Disable ssl check  for infradb.", type=bool)
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
