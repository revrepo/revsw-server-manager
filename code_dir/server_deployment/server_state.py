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
import time
import datetime

import paramiko

from copy import deepcopy

import re
from server_deployment.utilites import DeploymentError

import settings


logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class ServerState():
    """
    Class which contact with server and save state its deploy
    """

    def __init__(
            self, host_name, login, password,
            mongo_log, ipv4='', ipv6='', first_step="check_hostname"
    ):

        self.host_name = host_name
        self.start_time = datetime.datetime.now()
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.login = login
        self.password = password
        self.mongo_log = mongo_log
        self.server_constants = {
            "host_name": self.host_name,
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "login": self.login,
            "password": self.password,
            "udp_port_list": [],
            "tcp_port_list": [],
        }

        self.steps = {
            "reboot": None,
            "ping": None,

            "puppet_installed": None,
            "puppet_configured": None,
            "nagios_installed": None,
            "nagios_configured": None,
            "cacti_installed": None,
            "cacti_configured": None,
            "update": None,
            "upgrade": None
        }
        use_key = False
        if first_step not in [
            "check_hostname",
            "add_ns1_record",
            "add_to_infradb",
            "update_fw_rules",
            "install_puppet",
            "run_puppet"
        ]:
            use_key = True
        self.re_connect(using_key=use_key)

    def log_changes(self, log=None):
        pass
        # log_dict = deepcopy(self.steps)
        # log_dict.update(self.server_constants)
        # if log:
        #     log_dict['log'] = log
        # self.mongo_log.log(log_dict, step='host')

    def change_step_status(self, step, result, log=None):
        if step in self.server_constants.keys():
            self.steps[step] = result
            self.log_changes(log)
        else:
            raise DeploymentError("Log data not validate.")

    # reconect to server
    def re_connect(self, using_key=False):

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect = self.connection(self.login, password=self.password)
        if connect:
            return
        logger.info(
            'authentification with  custom credetials fail. '
            'trying to auth with default'
        )
        connect = self.connection(
            settings.DEFAULT_USERNAME,
            password=settings.DEFAULT_PASSWORD
        )
        if connect:
            return
        logger.info(
            'authentification with  default credetials '
            'fail. trying to auth with key'
        )
        connect = self.connection('robot', using_key=True)
        if connect:
            return
        raise DeploymentError("Problem with auth to server")

    def connection(self, username, password='', using_key=False):
        try:
            if using_key:
                k = paramiko.RSAKey.from_private_key_file(settings.KEY_PATH)
                self.client.connect(
                    hostname=self.ipv4,
                    username=username,
                    pkey=k,
                    port=22
                )
            else:
                self.client.connect(
                    hostname=self.ipv4,
                    username=username,
                    password=password,
                    port=22
                )
        except paramiko.BadAuthenticationType:
            return False
        return True

    def close_connection(self):
        self.client.close()

    def reboot(self, using_key=False):
        self.client.exec_command('sudo reboot')
        self.close_connection()
        time.sleep(settings.REBOOT_SLEEP_TIME)
        self.re_connect(using_key=using_key)

    # check hostname
    def check_hostname(self):
        (stdin_, stdout_, stderr_) = self.client.exec_command("hostname")
        time.sleep(2)  # sleep some time for complete command
        # status = stdout_.channel.recv_exit_status()
        lines = stdout_.readlines()

        for line in lines:
            logger.info("hostname %s" % line)
        return lines[0]

    def update_hostname(self, hostname):
        self.execute_command_with_log(
            "sudo echo -n %s > /etc/hostname" % hostname
        )

    def check_install_package(self, package_name):
        output = []
        (stdin, stdout, stderr) = self.client.exec_command(
            'dpkg -s %s' % package_name
        )
        for line in stdout.readlines():
            output.append(line)
        if output and output[1] == 'Status: install ok installed\n':
            return True
        return False

    def install_puppet(self):
        version = self.check_system_version()
        # version = '14.04'
        if version == '14.04':
            self.execute_command_with_log(
                'wget %s' % settings.PUPET_LINKS['14.04']
            )
            self.execute_command_with_log(
                'sudo dpkg -i puppetlabs-release-trusty.deb'
            )

        elif version == '16.04':
            self.execute_command_with_log(
                'wget %s' % settings.PUPET_LINKS['16.04']
            )
            self.execute_command_with_log(
                'sudo dpkg -i puppet-release-xenial.deb'
            )

        self.execute_command_with_log('sudo apt-get update')
        self.execute_command_with_log(
            'sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o '
            'Dpkg::Options::="--force-confdef" -o Dpkg::Options::='
            '"--force-confold" upgrade'
        )
        self.execute_command_with_log('sudo apt-get install puppet -y')
        logger.info(
            "Reboot server and  wait for %s "
            "seconds" % settings.REBOOT_SLEEP_TIME
        )
        self.reboot()
        puppet_installed = self.execute_command_with_log(
            'dpkg -l | grep puppet'
        )
        if puppet_installed != 0:
            log_error = "Server error. Status: %s Error: %s"
            self.mongo_log.log({"error_log": log_error})
            raise DeploymentError(log_error)

    def configure_puppet(self):
        self.execute_command_with_log('sudo puppet agent --enable')
        self.execute_command_with_log(
            'sudo puppet agent -t --server=%s' % settings.PUPPET_SERVER,
            check_status=False
        )

    def remove_puppet(self):
        logger.info('Removing puppet from server')
        self.execute_command_with_log(
            "pkill -9 puppet", check_status=False
        )
        self.execute_command_with_log(
            "sudo rm -r /var/lib/puppet/ssl", check_status=False
        )

    def run_puppet(self):
        logger.info(
            'sudo puppet agent -t --server=%s' % settings.PUPPET_SERVER
        )
        (stdin, stdout, stderr) = self.client.exec_command(
            'sudo puppet agent -t --server=%s' % settings.PUPPET_SERVER
        )
        lines = stdout.readlines()
        lines_list = []
        for line in lines:
            lines_list.append(line)
            logger.info(line)
        logger.info(
            "sudo puppet agent -t --server=%s was finished "
            "with code %s" % (
                settings.PUPPET_SERVER, stdout.channel.recv_exit_status()
            )
        )
        if stdout.channel.recv_exit_status() != 0 and \
            lines_list[0] == "Exiting; no certificate " \
                             "found and waitforcert is disabled":
            return 0
        return stdout.channel.recv_exit_status()

    def check_system_version(self):
        lines = []
        (stdin_v, stdout_v, stderr_v) = self.client.exec_command(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )
        for line in stdout_v.readlines():
            lines.append(line)
        try:
            m = re.search('DISTRIB_RELEASE=(.+?)$', lines[0])
        except AttributeError:
            return '14.04'
        if m:
            return m.group(1)
        return '14.04'

    def execute_command_with_log(self, command, check_status=True):
        logger.info(command)
        (stdin, stdout, stderr) = self.client.exec_command(command)
        lines = stdout.readlines()
        for line in lines:
            logger.info(line)
        if check_status and stdout.channel.recv_exit_status() != 0:
            log_error = "wrong status code after %s " % command
            self.mongo_log.log({"log": log_error})
            raise DeploymentError(log_error)
        logger.info(
            "%s was finished with code %s" % (
                command, stdout.channel.recv_exit_status()
            )
        )
        return stdout.channel.recv_exit_status()

    def check_ram_size(self):
        logger.info('Checking RAM size')
        (stdin, stdout, stderr) = self.client.exec_command(
            "grep 'MemTotal:'  /proc/meminfo"
        )
        lines = stdout.readlines()
        lines_list = []
        for line in lines:
            lines_list.append(line)
            logger.info(line)
        m = re.search('^MemTotal:\s*(.+?) kB', lines_list[0])
        ram_size = m.group(1)
        if int(ram_size) < (settings.REQUIRED_RAM_SIZE*1024):
            raise DeploymentError("Not enough RAM")

    def check_hw_architecture(self):
        logger.info('Checking HW architecture')
        (stdin, stdout, stderr) = self.client.exec_command("arch")
        lines = stdout.readlines()
        lines_list = []
        for line in lines:
            lines_list.append(line)
            logger.info(line)
        if lines_list[0].strip() != settings.REQUIRED_HW_ARCHITECTURE:
            raise DeploymentError('Wrong HW architecture')

    def check_os_version(self):
        logger.info('Checking OS version')
        lines = []
        (stdin_v, stdout_v, stderr_v) = self.client.exec_command(
            "cat /etc/lsb-release | grep DISTRIB_RELEASE"
        )
        for line in stdout_v.readlines():
            lines.append(line)
            logger.info(line)
        try:
            m = re.search('DISTRIB_RELEASE=(.+?)$', lines[0])
        except AttributeError:
            raise DeploymentError('Wrong OS version')
        if not m or m.group(1) != settings.REQUIRED_SYSTEM_VERSION:
            raise DeploymentError('Wrong OS version')

    def check_ping_8888(self):
        packet_lose = None
        logger.info('ping -f -c 1000 8.8.8.8')
        lines = []
        (stdin_v, stdout_v, stderr_v) = self.client.exec_command(
            "sudo ping -f -c 1000 8.8.8.8"
        )
        for line in stdout_v.readlines():
            lines.append(line)
            logger.info(line)
            m = re.search('1000 received, (.+?)% packet loss,', line)
            if m and m.group(1):
                packet_lose = m.group(1)
        if packet_lose != '0':
            raise DeploymentError('Problem with ping to  8.8.8.8')

    def check_free_space(self):
        free_space = None
        logger.info('Checking free space')
        lines = []
        (stdin_v, stdout_v, stderr_v) = self.client.exec_command("df")
        for line in stdout_v.readlines():
            lines.append(line)
            logger.info(line)
            m = re.search('(\d+?)\s+\d+% \/$', line.strip())
            if m and m.group(1):
                free_space = m.group(1)
        if int(free_space) < settings.REQUIRED_FREE_SPACE * 1024:
            raise DeploymentError(
                'Not enough free space. Need %s '
                'Mb and available only %s Mb' % (
                    settings.REQUIRED_FREE_SPACE,
                    int(free_space)/1024
                )
            )
