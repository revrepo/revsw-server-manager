import datetime
import time

import os
import paramiko
from copy import deepcopy
from jinja2 import Template, Environment, PackageLoader
from jinja2.loaders import FileSystemLoader

from code_dir import settings
from code_dir.server_deployment.utilites import DeploymentError


class Nagios():
    """
    Class which contact with server and save state its deploy
    """

    def __init__(self, host_name, mongo_log):

        self.host_name = host_name
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
        self.client.connect(hostname=self.server_name, username=self.login, password=self.password, port=22)
        return self.client.get_transport().is_active()

    def close_connection(self):
        self.client.close()

    def create_config_file(self, data):
        env = Environment(
            loader=FileSystemLoader(os.path.join(settings.BASE_DIR, "templates"))
        )
        template = env.get_template('nagios_config.jinja')
        result = template.render(**data)
        with open(os.path.join(settings.BASE_DIR, 'temp/%s.cfg' % self.host_name), 'w') as f:
            f.write(result)

    def send_config_to_server(self):
        sftp = self.client.open_sftp()
        sftp.put(
            os.path.join(settings.BASE_DIR, 'temp/%s.cfg' % self.host_name),
            os.path.join(settings.NAGIOS_CFG_PATH, '%s.cfg' % self.host_name)
        )
        self.mongo_log.log({"nagios_conf": "yes",}, "nagios")

    def reload_nagios(self):
        chan = self.client.exec_command("/etc/init.d/nagios reload")
        if chan.recv_exit_status() != 0:
            log_error = "Nagios reload error"
            self.mongo_log.log({"nagios_reload": "fail", "log": log_error}, "nagios")
            raise DeploymentError(log_error)
        self.mongo_log.log({"nagios_reload": "yes"}, "nagios")
