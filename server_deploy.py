
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
from server_deployment.infradb import InfraDBAPI

from server_deployment.mongo_logger import MongoLogger
from server_deployment.nsone_class import NsOneDeploy
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatic deployment of server.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--host_name", help="Host name of server", )
    parser.add_argument("-z", "--zone_name", help="Name of zone on NSONE.")
    parser.add_argument("-i", "--IP", help="IP of server.")
    parser.add_argument("-r", "--record_type", help="Type of record at NSONE.")
    parser.add_argument("-l", "--login", help="Login of the server.")
    parser.add_argument("-p", "--password", help="Password of the server.")
    parser.add_argument("-c", "--cert", help="Certificate of the server.")
    parser.add_argument("--location", help="Certificate of the server.")
    parser.add_argument("--hosting", help="Certificate of the server.")
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
        nsone = NsOneDeploy(host_name, host, logger)
        infradb = InfraDBAPI(
            settings.INFRADB_USERNAME, settings.INFRADB_PASSWORD, args.location, args.host_name, logger
        )

        # Start deploing of server
        server.check_hostname()

        # Reboot server to update hostname
        server.reboot()
        server.re_connect()

        # Add server to NS1
        nsone.add_new_monitor()
        zone = nsone.get_zone(zone_name)
        record = nsone.add_record(zone)
        record = nsone.get_record(zone, zone_name, record_type)
        server_versions = {
            "proxy_software_version": 1,
            "kernel_version": 1,
            "revsw_module_version": 1,
        }
        infradb.add_server(host_name, args.IP, server_versions)
    except DeploymentError as e:
        print e
        sys.exit(-1)
