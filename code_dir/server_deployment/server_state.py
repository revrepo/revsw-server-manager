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


import time
import datetime
import paramiko

from copy import deepcopy

import re
from server_deployment.utilites import DeploymentError

from code_dir import settings


class ServerState():
    """
    Class which contact with server and save state its deploy
    """

    def __init__(self, host_name, login, password, mongo_log, ipv4='', ipv6='', cert=''):

        self.host_name = host_name
        self.start_time = datetime.datetime.now()
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.login = login
        self.password = password
        self.cert = cert
        self.mongo_log = mongo_log
        self.server_constants = {
            "host_name": self.host_name,
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "login": self.login,
            "password": self.password,
            "cert": self.cert,
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

        self.re_connect()

    def log_changes(self, log=None):
        log_dict = deepcopy(self.steps)
        log_dict.update(self.server_constants)
        if log: log_dict['log'] = log
        self.mongo_log.log(log_dict, step='host')

    def change_step_status(self, step, result, log=None):
        if step in self.server_constants.keys():
            self.steps[step] = result
            self.log_changes(log)
        else:
            raise DeploymentError("Log data not validate.")

    # reconect to server and check connection status
    def re_connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.ipv4, username=self.login, password=self.password, port=22)
        return self.client.get_transport().is_active()

    def close_connection(self):
        self.client.close()

    def reboot(self):
        self.client.exec_command('sudo reboot')
        self.close_connection()
        time.sleep(120)

    # check hostname
    def check_hostname(self):
        stdin_, stdout_, stderr_ = self.client.exec_command("hostname")
        time.sleep(2) # sleep some time for complete command
        status = stdout_.channel.recv_exit_status()
        lines = stdout_.readlines()
        for line in lines:
            print 'hostname %s' % line
        return lines[0]

    # open and rewrite hostname file
    def set_hostname(self, hostname):
        ftp = self.client.open_sftp()
        file = ftp.file('/etc/hostname', "w", -1)
        file.write(hostname)
        file.flush()
        ftp.close()

    def check_install_package(self, package_name):
        output = []
        (stdin, stdout, stderr) = self.client.exec_command('dpkg -s %s' % package_name)
        for line in stdout.readlines():
            output.append(line)
        if output[1] == 'Status: install ok installed\n': return True

        return False

    def install_puppet(self):
        version = self.check_system_version()
        # version = '14.04'
        if version == '14.04':
            self.client.exec_command('wget %s' % settings.PUPET_LINKS['14.04'])
            self.client.exec_command('dpkg -i puppetlabs-release-trusty.deb')

        elif version == '16.04':
            self.client.exec_command('wget %s' % settings.PUPET_LINKS['16.04'])
            self.client.exec_command('dpkg -i puppet-release-xenial.deb')
        # (stdin, stdout, stderr) = self.client.exec_command("cat /etc/lsb-release | grep DISTRIB_RELEASE")


        self.client.exec_command('sudo apt-get update')
        self.client.exec_command('sudo apt-get upgrade -y')
        self.client.exec_command('sudo apt-get install puppet -y')

        self.reboot()
        self.re_connect()
        (stdin, stdout, stderr) = self.client.exec_command('dpkg -l | grep puppet')
        if stdout.channel.recv_exit_status() != 0:
            log_error = "Server error. Status: %s Error: %s"
            self.mongo_log.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)

    def configure_puppet(self):
        # (stdin, stdout, stderr) = self.client.exec_command("cat /etc/lsb-release | grep DISTRIB_RELEASE")
        self.client.exec_command('sudo puppet agent --enable')
        self.client.exec_command('sudo puppet agent -t --server=%s' % settings.PUPPET_SERVER)
        self.client.exec_command("sudo echo '[agent]' >> /etc/puppet/puppet.conf")
        self.client.exec_command("sudo echo 'server = %s' >> /etc/puppet/puppet.conf" % settings.PUPPET_SERVER)
        self.client.exec_command("sudo echo 'environment = production' >> /etc/puppet/puppet.conf")
        self.client.exec_command("sudo echo 'configtimeout = 600' >> /etc/puppet/puppet.conf")
        self.client.exec_command("sudo service puppet restart")


    def run_puppet(self):
        self.client.exec_command("sudo service puppet restart")
        (stdin, stdout, stderr) = self.client.exec_command("sudo service puppet status")

        if stdout.channel.recv_exit_status() != 0:
            log_error = "Server error. Status: %s Error: %s"
            self.mongo_log.log({"fw": "fail", "log": log_error}, "puppet")
            raise DeploymentError(log_error)

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