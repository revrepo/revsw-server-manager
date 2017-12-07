
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
import pymongo
import sys

import settings
from server_deployment.cds_api import CDSAPI
from server_deployment.infradb import InfraDBAPI

from server_deployment.mongo_logger import MongoLogger
from server_deployment.nsone_class import NsOneDeploy
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError


def deploy_cds(args, logger, server):
    # checking installed packages
    cds = CDSAPI(args.cdsgroup, args.host_name, logger)
    cds.check_installed_packages(server)

    cds_server = cds.check_server_exist()
    if cds_server:
        group_added = cds.check_server_in_group()
        check_list = cds.check_need_update_versions()
    else:
        group_added = False
        check_list = {
            'ssl': False,
            'waf_sdk': False,
            'domain_purge': False
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
        cds.add_server_to_group(host_name)
    if check_list['domain_purge']:
        cds.monitor_purge_and_domain_configuration()
    return cds.server_group


def remove_server_from_cds(args, logger):
    cds = CDSAPI(args.cdsgroup, args.host_name, logger)
    cds.update_server({"status": "offline"})
    cds.delete_server_from_groups()
    cds.delete_server()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Automatic deployment of server.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--host_name", help="Host name of server", )
    parser.add_argument("-z", "--zone_name", help="Name of zone on NSONE.")
    parser.add_argument("-i", "--IP", help="IP of server.")
    parser.add_argument("-r", "--record_type", help="Type of record at NSONE.", default="A")
    parser.add_argument("-l", "--login", help="Login of the server.")
    parser.add_argument("-p", "--password", help="Password of the server.", default='')
    parser.add_argument("-c", "--cert", help="Certificate of the server.")
    parser.add_argument("--location", help="Code of server location.")
    parser.add_argument("--hosting", help="Name of server hosting provider.")
    parser.add_argument(
        "--cdsgroup", help="CDS group."
    )
    parser.add_argument(
        "--environment", help="Environment of server.", default='staging'
    )
    args = parser.parse_args()

    try:
        logger = MongoLogger('test_host', datetime.datetime.now().isoformat())

        host_name = args.host_name
        host = args.IP
        zone_name = args.zone_name
        record_type = args.record_type
        server = ServerState(
            host_name, args.login, args.password,
            logger, ipv4=args.IP, cert=args.cert
        )
        nsone = NsOneDeploy(host_name, host_name, logger)
        infradb = InfraDBAPI(logger)

        # Start deploing of server
        server.check_hostname()

        # Reboot server to update hostname
        server.reboot()
        server.re_connect()

        # Add server to NS1
        zone = nsone.get_zone(zone_name)
        monitor_id = nsone.add_new_monitor()
        nsone.add_feed("c53f31f5e1817442d16b3eaac813a644")

        # record = nsone.add_record(zone)
        record = nsone.get_record(zone, zone_name, record_type)
        server_versions = {
            "proxy_software_version": 1,
            "kernel_version": 1,
            "revsw_module_version": 1,
        }
        infradb.add_server(host_name, args.IP, server_versions, args.location, args.host_name)

        # add server to cds
        group = deploy_cds(args, logger, server)
        # nsone.add_answer(zone, group['edge_host'], record_type)
        nsone.add_answer(zone, "test-alexus.attested.club", record_type, host)


    except DeploymentError as e:
        print e
        sys.exit(-1)
