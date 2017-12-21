
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
import pymongo
import sys

import re

import settings
from server_deployment.nagios import Nagios
from server_deployment.cds_api import CDSAPI
from server_deployment.infradb import InfraDBAPI

from server_deployment.mongo_logger import MongoLogger
from server_deployment.nsone_class import Ns1Deploy
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)

class DestroySequence():


    def __init__(self, args):

        self.steps = {
            "remove_from_nagios":self.remove_from_nagios,
            "remove_from_cds": self.remove_from_cds,
            "remove_ns1_monitor": self.remove_ns1_monitor,
            "remove_ns1_a_record": self.remove_ns1_a_record,
            "remove_from_infradb": self.remove_from_infradb,
            "remove_from_puppet": self.remove_from_puppet,
            "remove_ns1_balancing_rule": self.remove_ns1_balancing_rule,

        }
        self.step_sequence = [
            "remove_ns1_a_record",
            "remove_from_nagios",
            "remove_from_cds",
            "remove_ns1_monitor",
            "remove_from_infradb",
            "remove_from_puppet",
            "remove_ns1_balancing_rule"
        ]
        self.host_name = args.host_name
        self.server_group = args.server_group
        self.ip = args.IP
        self.first_step = args.first_step
        self.number_of_steps = args.number_of_steps_to_execute
        # self.dns_balancing_name = args.dns_balancing_name
        self.zone_name = self.get_zone_name()
        # self.zone_name = "attested.club"
        self.record_type = args.record_type

        self.logger = MongoLogger(self.host_name, datetime.datetime.now().isoformat())
        # self.server = ServerState(
        #     self.host_name, args.login, args.password,
        #    self.logger, ipv4=self.ip, first_step=self.first_step,
        # )
        self.ns1 = Ns1Deploy(self.host_name, self.host_name,self.logger)
        self.zone = self.ns1.get_zone(self.zone_name)
        self.infradb = InfraDBAPI(self.logger, ssl_disable=args.disable_infradb_ssl)
        self.short_name = self.get_short_name()

    def run_sequence(self):
        if self.first_step not in self.step_sequence:
            raise DeploymentError("Wrong first step")
        first_index = self.step_sequence.index(self.first_step)
        end_of_sequence = first_index + self.number_of_steps
        sequence_list = self.step_sequence[first_index:end_of_sequence]
        for step in sequence_list:
            logger.info("Running step %s" % step)
            self.steps[step]()

    def remove_from_nagios(self):
        nagios = Nagios(self.host_name, self.logger, self.short_name)
        nagios.delete_config_file()
        nagios.reload_nagios()

    def remove_from_cds(self):
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        server = cds.check_server_exist()
        if not server:
            logger.info("Server not exist in CDS")
            return
        logger.info('Turnoff server on cds')
        cds.update_server({"status": "offline"})
        logger.info('Deleting server from groups')
        cds.delete_server_from_groups()
        logger.info('Deleting server from cds')
        cds.delete_server()

    def remove_ns1_monitor(self):
        logger.info("Start server adding to NS1")
        monitor_id = self.ns1.check_is_monitor_exist()
        if not monitor_id:
            logger.info("NS1 monitor not exist")
            return
        self.ns1.delete_feed(settings.NS1_DATA_SOURCE_ID, monitor_id)
        self.ns1.delete_monitor(monitor_id)

    def remove_from_infradb(self):
        self.infradb.delete_server(self.host_name)

    def remove_ns1_a_record(self):
        logger.info("Deleting NS1 A record")

        record = self.ns1.get_a_record(
            self.zone, self.short_name, self.record_type
        )
        if not record:
            logger.info(' A record not found')
            return

        record.delete()
        logger.info("Record succesfully deleted")

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

        logger.info("command sudo puppet cert clean %s was executed with status %s" %
                    (self.host_name, stdout_fw.channel.recv_exit_status())
                    )
        if stdout_fw.channel.recv_exit_status() != 0:
            log_error = "Problem with removing from puppet."
            raise DeploymentError(log_error)
        logger.info("Server %s was deleted from puppet" % self.host_name)

    def remove_ns1_balancing_rule(self):
        logger.info("Getting dns balance name from CDS")
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        dns_balance_name = cds.server_group['edge_host']
        logger.info("DNS balancing name is %s" % dns_balance_name)
        logger.info("Getting DNS balance record")
        record = self.ns1.get_a_record(
            self.zone, dns_balance_name, self.record_type
        )
        if not record:
            logger.info(' A dns balance record not found')
            return
        new_answers = []
        logger.info("Deleting balance rule for  %s" % self.ip)
        for answer in record.data['answers']:
            if answer['answer'] != [self.ip]:
                new_answers.append(answer)
        record.update(answers=new_answers)
        logger.info("DNS balancing rules succesfuly changed")

    def get_short_name(self):
        m = re.search('^(.+?)\.', self.host_name)
        if m:
            return m.group(1)
        raise DeploymentError("Wrong Host_name")

    def get_zone_name(self):
        m = re.search('^[a-zA-Z0-9_]*-[a-zA-Z0-9_]*.(.+?)$', self.host_name)
        if m:
            return m.group(1)
        raise DeploymentError("Wrong Host_name")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Automatic deployment of server.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--host_name", help="Host name of server", required=True)
    parser.add_argument("-z", "--zone_name", help="Name of zone on NS1.", default=settings.NS1_DNS_ZONE_DEFAULT)
    parser.add_argument("-i", "--IP", help="IP of server.", required=True)
    parser.add_argument("-r", "--record_type", help="Type of record at NS1.", default="A")
    parser.add_argument("-l", "--login", help="Login of the server.", default="robot")
    parser.add_argument("-p", "--password", help="Password of the server.", default='')
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
        "--first_step", help="First step which sequence must start.", default='remove_from_nagios',
        choices=[
            "remove_ns1_a_record",
            "remove_from_nagios",
            "remove_from_cds",
            "remove_ns1_monitor",
            "remove_from_infradb",
            "remove_from_puppet",
            "remove_ns1_balancing_rule"
        ]
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
        sequence = DestroySequence(args)
        sequence.run_sequence()

    except DeploymentError as e:
        logger.critical(e.message)
        logger.error(e, exc_info=True)
        sys.exit(-1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(-1)
