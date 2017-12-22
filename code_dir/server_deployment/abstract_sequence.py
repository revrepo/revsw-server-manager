
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
import datetime

import paramiko
import re

import settings
from server_deployment.infradb import InfraDBAPI
from server_deployment.mongo_logger import MongoLogger
from server_deployment.nsone_class import Ns1Deploy
from server_deployment.server_state import ServerState

from code_dir.server_deployment.utilites import DeploymentError

# logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class SequenceAbstract(object):

    def __init__(self, args):

        # required aruments is host_name, ip, first_step, number_of_steps, login, pasword, disable_infradb_ssl

        self.steps = {}  # dict for associate name of step and method
        self.step_sequence = []  # list of steps
        self.host_name = args.host_name
        self.short_name = self.get_short_name()
        self.ip = args.IP
        self.first_step = args.first_step
        self.number_of_steps = args.number_of_steps_to_execute
        self.location_code = self.get_location_code()
        self.zone_name = self.get_zone_name()
        # self.zone_name = "attested.club"
        self.logger = MongoLogger(
            self.host_name, datetime.datetime.now().isoformat()
        )

        self.ns1 = Ns1Deploy(self.host_name, self.ip, self.logger)
        self.zone = self.ns1.get_zone(self.zone_name)
        self.infradb = InfraDBAPI(
            self.logger, ssl_disable=args.disable_infradb_ssl
        )

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
        logger.info("Server %s was deleted from puppet" % self.host_name)
        return stdout_fw.channel.recv_exit_status()

    def run_sequence(self):
        if self.first_step not in self.step_sequence:
            raise DeploymentError("Wrong first step")
        first_index = self.step_sequence.index(self.first_step)
        end_of_sequence = first_index + self.number_of_steps
        sequence_list = self.step_sequence[first_index:end_of_sequence]
        for step in sequence_list:
            logger.info("Running step %s" % step)
            self.steps[step]()

    def get_location_code(self):
        m = re.search('^(.+?)-', self.host_name)
        if m:
            return m.group(1)
        raise DeploymentError("Wrong Host_name")

