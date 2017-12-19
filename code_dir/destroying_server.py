
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
from server_deployment.nsone_class import NsOneDeploy
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
            "remove_from_nsone": self.remove_from_nsone,
            "remove_from_infradb": self.remove_from_infradb

        }
        self.step_sequence = [
            "remove_from_nagios",
            "remove_from_cds",
            "remove_from_nsone",
            "remove_from_infradb"
        ]
        self.host_name = args.host_name
        self.server_group = args.server_group
        self.ip = args.IP
        self.first_step = args.first_step
        self.number_of_steps = args.number_of_steps_to_execute
        # self.dns_balancing_name = args.dns_balancing_name
        # self.zone_name = args.zone_name
        self.record_type = args.record_type

        self.logger = MongoLogger(self.host_name, datetime.datetime.now().isoformat())
        # self.server = ServerState(
        #     self.host_name, args.login, args.password,
        #    self.logger, ipv4=self.ip, first_step=self.first_step,
        # )
        self.nsone = NsOneDeploy(self.host_name, self.host_name,self.logger)
        # self.zone = self.nsone.get_zone(self.zone_name)
        self.infradb = InfraDBAPI(self.logger, ssl_disable=args.disable_infradb_ssl)


        # self.location_code = self.get_location_code()

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
        pass

    def remove_from_cds(self):
        cds = CDSAPI(self.server_group, self.host_name, self.logger)
        logger.info('Turnoff server on cds')
        cds.update_server({"status": "offline"})
        logger.info('Deleting server from groups')
        cds.delete_server_from_groups()
        logger.info('Deleting server from cds')
        cds.delete_server()

    def remove_from_nsone(self):
        pass

    def remove_from_infradb(self):
        pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Automatic deployment of server.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--host_name", help="Host name of server", required=True)
    parser.add_argument("-z", "--zone_name", help="Name of zone on NSONE.", default=settings.NS1_DNS_ZONE_DEFAULT)
    parser.add_argument("-i", "--IP", help="IP of server.", required=True)
    parser.add_argument("-r", "--record_type", help="Type of record at NSONE.", default="A")
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
        "--first_step", help="First step which sequence must start.", default='check_hostname',
        choices=[
            "remove_from_nagios",
            "remove_from_cds",
            "remove_from_nsone",
            "remove_from_infradb"
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