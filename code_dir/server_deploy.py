
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

import paramiko
import pymongo
import sys

import settings
from code_dir.server_deployment.nagios import Nagios
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
        cds.add_server_to_group()
    if check_list['domain_purge']:
        cds.monitor_purge_and_domain_configuration()
    return cds.server_group


def update_fw_rules(logger):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=settings.INSTALL_SERVER_HOST,
        username=settings.INSTALL_SERVER_LOGIN,
        password=settings.INSTALL_SERVER_PASSWORD,
        port=22
    )
    stdin_fw, stdout_fw, stderr_fw = client.exec_command("sh /opt/revsw-firewall-manager/update_all.sh")
    if stdout_fw.channel.recv_exit_status() != 0:
        log_error = "Problem with FW rules update on INSTALL server"
        logger.log({"fw": "fail", "log": log_error}, "puppet")
        raise DeploymentError(log_error)
    stdin_pu, stdout_pu, stderr_pu = client.exec_command("puppet agent -t")
    if stdout_pu.channel.recv_exit_status() != 0:
        log_error = "Problem with pupprt agent on INSTALL server"
        logger.log({"fw": "fail", "log": log_error}, "puppet")
        raise DeploymentError(log_error)
    client.close()


def sign_ssl_puppet(logger, host_name):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=settings.INSTALL_SERVER_HOST,
        username=settings.INSTALL_SERVER_LOGIN,
        password=settings.INSTALL_SERVER_PASSWORD,
        port=22
    )
    stdin_fw, stdout_fw, stderr_fw = client.exec_command("puppet cert sign %s" % host_name)
    if stdout_fw.channel.recv_exit_status() != 0:
        log_error = "Problem with FW rules update on INSTALL server"
        logger.log({"fw": "fail", "log": log_error}, "puppet")
        raise DeploymentError(log_error)
    client.close()


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
    parser.add_argument("--location", help="Code of server location.", default="TESTSJC20")
    parser.add_argument(
        "--hosting", help="Name of server hosting provider.", default="HE Fremont 2 Facility"
    )
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
        print server.check_system_version()
        nsone = NsOneDeploy(host_name, host_name, logger)
        infradb = InfraDBAPI(logger)

        # Start deploing of server
        print "\n\n Checkin hostname"
        server.check_hostname()

        # Reboot server to update hostname
        print "\n\n reboot server"
        server.reboot()
        server.re_connect()

        # Add server to NS1
        print "\n\n Start server adding to NS1"
        zone = nsone.get_zone(zone_name)
        monitor_id = nsone.add_new_monitor()
        print 'New monitor id %s' % monitor_id
        nsone.add_feed(settings.NS1_DATA_SOURCE_ID)

        record = nsone.add_record(zone)
        print "NS1 record id %s" % record['id']
        # record = nsone.get_record(zone, zone_name, record_type)
        server_versions = {
            "proxy_software_version": 1,
            "kernel_version": 1,
            "revsw_module_version": 1,
        }
        print '\n\nAdding server to inradb'
        infradb.add_server(host_name, args.IP, server_versions, args.location, args.host_name)


        #upgade FW rules
        print '\n\nUpgrade FW rules.'
        update_fw_rules(logger)

        # install puppet
        print '\n\nInstall and run puppet.'
        server.install_puppet()
        server.configure_puppet()
        server.run_puppet()
        sign_ssl_puppet(logger, host_name)
        server.run_puppet()

        # add server to cds
        group = deploy_cds(args, logger, server)

        #NAGIOS configurate

        nagios = Nagios(host_name, logger)
        nagios_data = {
            'host_name': host_name,
            "ip": host,
        }
        nagios.create_config_file(nagios_data)
        nagios.send_config_to_server()


        print '\n\n Add answer to NS1 to record %s' % group['edge_host']
        # nsone.add_answer(zone, group['edge_host'], record_type)
        nsone.add_answer(zone, "test-alexus.attested.club", record_type, host)


    except DeploymentError as e:
        print e
        sys.exit(-1)
