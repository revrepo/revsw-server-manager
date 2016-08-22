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
from nsone import Nsone
from proxy import Proxy
from nagios import Nagios
import traceback
from sys import argv
import settings
from pprint import pprint


# logging.basicConfig(level=logging.DEBUG, format='%(levelname)-9s %(name)s: %(message)s')

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('RS')
#logger.setLevel(logging.DEBUG)


def print_help():
    usage = """RevSoft server control. 
    
That's what you can do with it:
    rs help - print help, the exact same help you are looking at.
    rs suspend SERVER1 <SERVER2 ...> - suspend traffic on those servers.
    rs resume SERVER1 <SERVER2 ...> - resume traffic on those servers.
    rs upgrade REMOTE_UPGRADE_BASH_SCRIPT REMOTE_TEST_BASH_SCRIPT SERVER1 <SERVER2 ...> - perform a full upgrade procedure on those servers.
    rs wait_low_traffic SERVER1 <SERVER2 ...> - hang until servers reached low traffic.
    rs force_upgrade <REMOTE_UPGRADE_BASH_SCRIPT> <REMOTE_TEST_BASH_SCRIPT> SERVER1 <SERVER2 ...> - quick upgrade, no resume or suspend of traffic.
    rs check_traffic SERVER1 <SERVER2 ...> - check traffic figures on those servers.
    rs test REMOTE_TEST_BASH_SCRIPT SERVER1 <SERVER2 ...> - execute test script against those servers.
    rs nagios_state <SERVER1 ...>- display nagios state. If a server list is provided, it will filter the results.
    rs schedule_downtime SERVER1 <SERVER2 ...> - Declare scheduled downtime in nagios.
    rs cancel_downtime SERVER1 <SERVER2 ...> - Remove declared scheduled downtime in nagios.
    rs upload_file LOCAL_FILE REMOTE_FILE SERVER1 <SERVER2 ...> - Upload a file to those servers
"""
    logger.info(usage)


def wait_low_traffic(server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        p.wait_low_traffic()


def check_traffic(server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        rps, out = p.check_traffic()
        del p
        print "RPS: %d OUT: %d" % (rps, out)


def suspend(server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        p.suspend()


def resume(server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        p.resume()


def upgrade(server_list, remote_upgrade_script=None, remote_test_script=None):
    if remote_upgrade_script:
        settings.UPGRADE_COMMAND = "sudo bash %s" % remote_upgrade_script

    if remote_test_script:
        settings.PROXY_TEST_COMMAND = "sudo bash %s" % remote_test_script

    for server_name in server_list:
        p = Proxy(server_name)
        p.upgrade()


def force_upgrade(server_list, remote_upgrade_script=None, remote_test_script=None):
    if remote_upgrade_script:
        settings.UPGRADE_COMMAND = "sudo bash %s" % remote_upgrade_script

    if remote_test_script:
        settings.PROXY_TEST_COMMAND = "sudo bash %s" % remote_test_script

    for server_name in server_list:
        p = Proxy(server_name)
        p.force_upgrade()


def test(remote_test_script, server_list):
    if remote_test_script:
        settings.PROXY_TEST_COMMAND = "sudo bash %s" % remote_test_script

    for server_name in server_list:
        p = Proxy(server_name)
        p.test()


def nagios_state(server_list=set()):
    upper_server_list = set()
    for s in server_list:
        upper_server_list.add(s.upper())

    nagios = Nagios()
    state = nagios.get_state()
    for server_name, server_data in state.items():
        if upper_server_list and server_name.upper() not in upper_server_list:
            continue
        print "%s\n%s" % (server_name,len(server_name) * "=")
        current_state = server_data['current_state']
        print "current state: %s" % current_state
        last_check = server_data['last_check']
        if len(server_data['services']) > 0:
            print " Services:"
            for service_name, service_data in server_data['services'].items():
                print "  %s: %s" % (service_name, service_data['current_state'])
#         for k in state[server].keys():
#             print " %s: %s" % (k,state[server][k])


def nagios_schedule_downtime(server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        p.nagios_schedule_downtime()


def upload_file(local_file, remote_file, server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        p.upload_file(local_file, remote_file)


def nagios_cancel_downtime(server_list):
    for server_name in server_list:
        p = Proxy(server_name)
        p.nagios_cancel_downtime()


def print_help_exit_error():
    print_help()
    exit(1)


def error_server_list():
    logger.error("Please provide a space separated list of one or more servers to process.")
    exit(1)
    
if __name__ == "__main__":
    if len(argv) == 1:
        print_help_exit_error()
    try:
        cmd = argv[1]
        
        if cmd == "help":
            print_help_exit_error()
        elif cmd == "wait_low_traffic":
            if len(argv) < 3:
                error_server_list()
            wait_low_traffic(argv[2:])
        elif cmd == "check_traffic":
            if len(argv) < 3:
                error_server_list()
            check_traffic(argv[2:])
        elif cmd == "suspend":
            if len(argv) < 3:
                error_server_list()
            suspend(argv[2:])
        elif cmd == "resume":
            if len(argv) < 3:
                error_server_list()
            resume(argv[2:])
        elif cmd == "upgrade":
            if len(argv) < 3:
                error_server_list()

            if len(argv) == 5:
                upgrade(
                    argv[4:],
                    remote_upgrade_script=argv[2],
                    remote_test_script=argv[3]
                )
            else:
                upgrade(argv[2:])

        elif cmd == "force_upgrade":
            if len(argv) < 3:
                error_server_list()

            if len(argv) == 5:
                force_upgrade(
                    argv[4:],
                    remote_upgrade_script=argv[2],
                    remote_test_script=argv[3]
                )
            else:
                force_upgrade(argv[2:])

        elif cmd == "test":
            if len(argv) < 4:
                error_server_list()
            test(argv[2], argv[3:])
        elif cmd == "nagios_state":
            if len(argv) < 3:
                nagios_state()
            else:
                nagios_state(argv[2:])
        elif cmd == "schedule_downtime":
            if len(argv) < 3:
                error_server_list()
            nagios_schedule_downtime(argv[2:])
        elif cmd == "cancel_downtime":
            if len(argv) < 3:
                error_server_list()
            nagios_cancel_downtime(argv[2:])
        elif cmd == "upload_file":
            if len(argv) < 4:
                logger.error("Please provide a name of a local file to upload, a remote location for that file, "
                             "and a list of server you would like to upload the file to.")
                exit(1)
            if len(argv) < 5:
                error_server_list()
            upload_file(argv[2], argv[3], argv[4:])
                        
        # """ Undocumented testing stuff here """
        elif cmd == "_nsone_monitoring_jobs":
            nsone = Nsone()
            pprint(nsone.get_monitoring_jobs())
        elif cmd == "_get_nsone_monitoring_job":
            nsone = Nsone()
            pprint(nsone.get_monitoring_jobs_by_host(argv[2]))
        elif cmd == "_nsone_fail_server":
            nsone = Nsone()
            pprint(nsone.fail_status_monitoring_jobs(argv[2]))
        elif cmd == "_nsone_unfail_server":
            nsone = Nsone()
            pprint(nsone.unfail_status_monitoring_jobs(argv[2]))
        else:
            print "Not sure what you were trying to do. Here is the usage help.\n\n"
            print_help_exit_error()
    except Exception, e:
        logger.fatal(traceback.format_exc())
        exit(1)
