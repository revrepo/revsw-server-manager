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

import re
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

import settings
from nagios import Nagios
from server_deployment.utilites import DeploymentError


logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class Cacti():
    """
    Class which contact with server and save state its deploy
    """

    def __init__(self, host_name, mongo_log, short_name):

        self.host_name = host_name
        self.short_name = short_name
        self.login = settings.CACTI_SERVER_LOGIN
        self.server_name = settings.CACTI_SERVER
        self.password = settings.CACTI_SERVER_PASSWORD
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

    def add_device(self):
        logger.info('Adding new device to cacti.')
        logger.info('Checking if device already added')
        host_id = self.find_device(self.short_name)
        if host_id:
            print 'Device already added'
            return host_id
        logger.info('Device not exist.')
        # self.client.exec_command('cd ')
        template_id = self.find_host_template(settings.CACTI_HOST_TEMPLATE)
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_device.php --description=%s --ip=%s --community=%s --template=%s" % (
                self.short_name, self.host_name, settings.CACTI_SNMP_COMMUNITY_NAME, template_id
            )
        )
        output = []
        lines = stdout_fw.readlines()
        for line in lines:
            output.append(line)
            logger.info(line)
        if stdout_fw.channel.recv_exit_status() != 0:
            raise DeploymentError("Some problems with adding device")
        logger.info(output)
        try:
            m = re.search('Success - new device-id: \((.+?)\)', output[1])
        except AttributeError:
            raise DeploymentError("Some problems with adding device")
        if m:
            return m.group(1)

    def find_host_template(self, name):
        logger.info("Find host template with name %s" % name)
        logger.info("sudo php -q /usr/share/cacti/cli/add_device.php --list-host-templates")
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_device.php --list-host-templates"
        )
        output = []
        template_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                template_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not template_id:
            raise DeploymentError('Template %s not found in cacti' % name)
        logger.info('Template was  found with id %s' % template_id)
        return template_id

    def find_device(self, name):
        logger.info("Find device with name %s" % name)
        logger.info("sudo php -q /usr/share/cacti/cli/add_graphs.php --list-hosts")
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-hosts"
        )
        output = []
        host_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                host_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        return host_id

    def find_graph_template(self, name):
        logger.info("Find graph template with name %s" % name)
        logger.info("sudo php -q /usr/share/cacti/cli/add_graphs.php --list-graph-templates")
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-graph-templates"
        )
        output = []
        template_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                template_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not template_id:
            raise DeploymentError('Template %s not found in cacti' % name)
        logger.info('Template was  found with id %s' % template_id)
        return template_id

    def add_graph(self, graph_template_name, host_id):
        logger.info("Adding new graph")
        additional_params = ''
        template_id = self.find_graph_template(graph_template_name)
        graph_type = "cg"
        if graph_template_name == "Interface - Traffic (bits/sec)":
            snmp_query_id = self.find_snmp_querie('SNMP - Interface Statistics')
            additional_params += " --snmp-query-id=%s" % snmp_query_id
            query_type = self.find_snmp_querie_type("In/Out Bits (64-bit Counters)", snmp_query_id)
            additional_params += " --snmp-query-type-id=%s" % query_type
            snmp_field = 'ifIP'
            additional_params += " --snmp-field=%s" % snmp_field
            snmp_value = self.find_value(host_id, '192', snmp_field)
            additional_params += " --snmp-value=%s" % snmp_value
            graph_type = 'ds'
        elif graph_template_name == 'ucd/net - Available Disk Space':
            snmp_query_id = self.find_snmp_querie('ucd/net -  Get Monitored Partitions')
            additional_params += " --snmp-query-id=%s" % snmp_query_id
            query_type = self.find_snmp_querie_type("Available/Used Disk Space", snmp_query_id)
            additional_params += " --snmp-query-type-id=%s" % query_type

            snmp_field = 'dskDevice'
            additional_params += ' --snmp-field=%s' % snmp_field
            snmp_value = self.find_value(host_id, '/dev', snmp_field)
            additional_params += ' --snmp-value=%s' %snmp_value
            graph_type = 'ds'
        logger.info(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --graph-type=%s --graph-template-id=%s --host-id=%s %s" % (
                graph_type, template_id, host_id, additional_params
            )
        )
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            'sudo php -q /usr/share/cacti/cli/add_graphs.php --graph-type=%s --graph-template-id=%s --host-id=%s %s' % (
                graph_type, template_id, host_id, additional_params
            )
        )
        output = []
        lines = stdout_fw.readlines()
        for line in lines:
            output.append(line)
            logger.info(line)
        if stdout_fw.channel.recv_exit_status() != 0:
            raise DeploymentError("Some problems with adding graph")
        logger.info(output)
        try:
            m = re.search('Graph Added - graph-id: \((.+?)\) ', output[0])
        except AttributeError:
            raise DeploymentError("Some problems with adding graph")
        if m:
            return m.group(1)

    def find_tree(self, name):
        logger.info("Find tree with name %s" % name)
        logger.info("sudo php -q /usr/share/cacti/cli/add_tree.php --list-trees")
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_tree.php --list-trees"
        )
        output = []
        tree_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                tree_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not tree_id:
            raise DeploymentError('Tree %s not found in cacti' % name)
        logger.info('Tree was  found with id %s' % tree_id)
        return tree_id

    def find_graph(self, host_id, name):
        logger.info("Find graphs for host %s" % host_id)
        logger.info("sudo php -q /usr/share/cacti/cli/add_perms.php --list-graphs --host-id=%s" % host_id)
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_perms.php --list-graphs --host-id=%s" % host_id
        )
        output = []
        tree_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                tree_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not tree_id:
            return tree_id
        logger.info('Graph was  found with id %s' % tree_id)
        return tree_id

    def find_value(self, host_id, name, field):
        logger.info("Finding values  for host %s" % host_id)
        logger.info(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-values  --host-id=%s --snmp-field=%s" % (
                host_id, field
            )
        )
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-values  --host-id=%s --snmp-field=%s" % (
                host_id, field
            )
        )
        output = []
        tree_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                tree_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not tree_id:
            raise DeploymentError('Value %s not found in cacti' % name)
        logger.info('Graph was  found with id %s' % tree_id)
        return tree_id

    def find_snmp_querie(self, name):
        logger.info("Find snmp querie with name %s" % name)
        logger.info("sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-queries")
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-snmp-queries"
        )
        output = []
        quer_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                quer_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not quer_id:
            raise DeploymentError('snmp-querie %s not found in cacti' % name)
        logger.info('snmp-queries was  found with id %s' % quer_id)
        return quer_id

    def find_snmp_querie_type(self, name, query_id):
        logger.info("Find snmp querie type with name %s" % name)
        logger.info("sudo php -q /usr/share/cacti/cli/add_graphs.php --list-query-types  --snmp-query-id=%s" % query_id)
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_graphs.php --list-query-types  --snmp-query-id=%s" % query_id
        )
        output = []
        type_id = None
        lines = stdout_fw.readlines()
        for line in lines:
            if name in line:
                splited_line = line.split('\t')
                type_id = splited_line[0]
            output.append(line)
            logger.info(line)
        logger.info(output)
        if not type_id:
            raise DeploymentError('snmp-querie type %s not found in cacti' % name)
        logger.info('snmp-queries type was  found with id %s' % type_id)
        return type_id

    def add_graph_to_tree(self, graph_id):
        logger.info("Adding graph to tree")
        tree_id = self.find_tree(settings.CACTI_TREE_NAME)
        stdin_fw, stdout_fw, stderr_fw = self.client.exec_command(
            "sudo php -q /usr/share/cacti/cli/add_tree.php --type=node --node-type=graph --tree-id=%s --graph-id=%s" % (
                tree_id, graph_id
            )
        )
        output = []
        lines = stdout_fw.readlines()
        for line in lines:
            output.append(line)
            logger.info(line)
        if stdout_fw.channel.recv_exit_status() != 0:
            raise DeploymentError("Some problems with adding graph")
        logger.info(output)
        try:
            m = re.search('Added Node node-id: \((.+?)\)', output[0])
        except AttributeError:
            raise DeploymentError("Some problems with adding graph")
        if m:
            return m.group(1)