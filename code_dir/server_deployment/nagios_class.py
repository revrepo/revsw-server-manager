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

import os
import paramiko
import time
from copy import deepcopy

from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

import settings
from nagios import Nagios
from server_deployment.utilites import DeploymentError


logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class NagiosServer():
    """
    Class which contact with server and save state its deploy
    """

    def __init__(self, host_name, mongo_log, short_name):

        self.host_name = host_name
        self.short_name = short_name
        self.login = settings.NAGIOS_SERVER_LOGIN
        self.server_name = settings.NAGIOS_SERVER
        self.password = settings.NAGIOS_SERVER_PASSWORD
        self.mongo_log = mongo_log
        self.server_constants = {
            "host_name": self.host_name,
            "login": self.login,
            "password": self.password,
        }

        self.steps = {
            "nagios_config": False
        }

        self.re_connect()
        self.nagios_api = Nagios()

    def log_changes(self, log=None):
        log_dict = deepcopy(self.steps)
        log_dict.update(self.server_constants)
        if log:
            log_dict['log'] = log

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
        self.client.connect(
            hostname=self.server_name,
            username=self.login,
            password=self.password,
            port=22
        )
        return self.client.get_transport().is_active()

    def close_connection(self):
        self.client.close()

    def create_config_file(self, data):
        logger.info("Create nagios conf file")
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(
                    settings.BASE_DIR, "server_deployment/templates"
                )
            )
        )
        template = env.get_template('nagios_config.jinja')
        result = template.render(**data)
        with open('/tmp/%s.cfg' % self.short_name, 'w') as f:
            f.write(result)

    def send_config_to_server(self):
        logger.info("Send file to server")
        sftp = self.client.open_sftp()
        sftp.put(
            os.path.join(
                settings.BASE_DIR, '/tmp/%s.cfg' % self.short_name
            ),
            os.path.join(
                settings.NAGIOS_TEMP_CFG_PATH, '%s.cfg' % self.short_name
            )
        )
        self.execute_command_with_log("sudo mv %s %s" % (
            os.path.join(
                settings.NAGIOS_TEMP_CFG_PATH, '%s.cfg' % self.short_name
            ),
            os.path.join(
                settings.NAGIOS_CFG_PATH, '%s.cfg' % self.short_name))
                                      )

    def delete_config_file(self):
        logger.info("Delete nagios conf file")
        self.execute_command_with_log(
            "sudo rm %s" % os.path.join(
                settings.NAGIOS_CFG_PATH,
                '%s.cfg' % self.short_name
            ),
            check_status=False
        )

    def reload_nagios(self):
        logger.info("Reloading nagios")
        chan = self.execute_command_with_log("sudo /etc/init.d/nagios reload")
        if chan != 0:
            log_error = "Nagios reload error"
            self.mongo_log.log(
                {"nagios_reloaded": "fail", "error_log": log_error},
                "add_to_nagios"
            )
            raise DeploymentError(log_error)

    def check_nagios_config(self):

        return self.execute_command_with_log(
            "sudo /etc/init.d/nagios checkconfig"
        )

    def execute_command_with_log(self, command, check_status=True):
        logger.info(command)
        (stdin, stdout, stderr) = self.client.exec_command(command)
        lines = stdout.readlines()
        for line in lines:
            logger.info(line)
        if check_status and stdout.channel.recv_exit_status() != 0:
            log_error = "wrong status code after %s " % command
            raise DeploymentError(log_error)
        logger.info(
            "%s was finished with code %s" % (
                command, stdout.channel.recv_exit_status()
            ))
        return stdout.channel.recv_exit_status()

    def check_services_status(self):
        self.nagios_api.forced_schedule_check(self.short_name)
        time.sleep(settings.NAGIOS_FORCING_CHECK_SERVICES_WAIT_TIME)
        services = self.nagios_api.get_services_by_host(self.short_name)
        for service_name, service_data in services.iteritems():
            if service_name in settings.IGNORE_NAGIOS_SERVICES:
                continue

            if service_data['last_hard_state'] != "0":
                raise DeploymentError("Service %s is not UP" % service_name)

    def get_host(self):
        return self.nagios_api.get_host(self.short_name)
