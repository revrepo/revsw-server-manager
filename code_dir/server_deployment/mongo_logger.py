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
import datetime
import pymongo
import settings

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from server_deployment.utilites import DeploymentError


class MongoLogger():

    schema = {
        "type": "object",
        "properties": {
            "time": {"type": "string"},
            "start_time": {"type": "string"},
            "initial_data": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string"},
                    "ip": {
                        "type": "string",
                        "pattern": "(([0-9]|[1-9][0-9]|1[0-9]"
                                   "{2}|2[0-4][0-9]|25[0-5])\.)"
                                   "{3}([0-9]|[1-9][0-9]|1[0-9]"
                                   "{2}|2[0-4][0-9]|25[0-5])"
                    },
                    "login": {"type": "string"},
                    "password": {"type": "string"},

                }
            },
            "check_server_consistency": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "check_ram_size": {"type": "string", "pattern": "yes|no|fail"},
                    "check_free_space": {"type": "string", "pattern": "yes|no|fail"},
                    "check_hw_architecture": {"type": "string", "pattern": "yes|no|fail"},
                    "check_os_version": {"type": "string", "pattern": "yes|no|fail"},
                    "check_ping_8888": {"type": "string", "pattern": "yes|no|fail"},
                    "hostname": {"type": "string"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "check_hostname": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    'hostname_checked': {"type": "string", "pattern": "yes|no|fail"},
                    "server_rebooted": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_ns1_a_record": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "adding_record": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_to_infradb": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "server_added": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "update_fw_rules": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "install_puppet": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "puppet_installed": {"type": "string", "pattern": "yes|no|fail"},
                    "puppet_configured": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "run_puppet": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "puppet_runned": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_to_cds": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "server_group": {"type": "string", "pattern": "yes|no|fail"},
                    "check_server_exist": {"type": "string", "pattern": "yes|no|fail"},
                    "server_add": {"type": "string", "pattern": "yes|no|fail"},
                    "check_packages": {"type": "string", "pattern": "yes|no|fail"},
                    "install_ssl_configuration": {"type": "string", "pattern": "yes|no|fail"},
                    "install_waf_and_sdk_configuration": {"type": "string", "pattern": "yes|no|fail"},
                    "install_purge_and_domain_configuration": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_to_nagios": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "file_created": {"type": "string", "pattern": "yes|no|fail"},
                    "file_loaded": {"type": "string", "pattern": "yes|no|fail"},
                    "nagios_reloaded": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_ns1_monitor": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "monitor_added": {"type": "string", "pattern": "yes|no|fail"},
                    "monitor_up": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_ns1_balancing_rule": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "answer_added": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
            "add_to_pssh_file": {
                "type": "object",
                "properties": {
                    "runned": {"type": "string", "pattern": "yes|no|fail"},
                    "server_added": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"},
                    "error_log": {"type": "string"}  # [|if returned code !=0]
                },
            },
        },
        "required": [
            "time",
            "start_time",
            "initial_data",
            "check_server_consistency",
            "check_hostname",
            "add_ns1_a_record",
            "add_to_infradb",
            "update_fw_rules",
            "install_puppet",
            "run_puppet",
            "add_to_cds",
            "add_to_nagios",
            "add_ns1_monitor",
            "add_ns1_balancing_rule",
            "add_to_pssh_file",
        ]
    }

    def __init__(self, host_name, start_time, initial_data):
        self.mongo_cli = pymongo.MongoClient(
            settings.MONGO_HOST, settings.MONGO_PORT
        )
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]

        self.log_collection = self.mongo_db[host_name]
        self.log_collection.ensure_index('notification',sparse=True)
        self.current_server_state = {
            "start_time": start_time,
            "time": None,
            "initial_data": initial_data,
            "check_server_consistency": {
                "runned": "no",
            },
            "check_hostname": {
                "runned": "no",
            },
            "add_ns1_a_record": {
                "runned": "no",
            },
            "add_to_infradb": {
                "runned": "no",
            },
            "update_fw_rules": {
                "runned": "no",
            },
            "install_puppet": {
                "runned": "no",
            },
            "run_puppet": {
                "runned": "no",
            },
            "add_to_cds": {
                "runned": "no",
            },
            "add_to_nagios": {
                "runned": "no",
            },
            "add_ns1_monitor": {
                "runned": "no",
            },
            "add_ns1_balancing_rule": {
                "runned": "no",
            },
            "add_to_pssh_file": {
                "runned": "no",
            },
        }
        self.log_collection.insert_one(self.current_server_state)

    def log(self, log_dict, step):
        if step not in self.current_server_state.keys():
            raise DeploymentError("Wrong logging keys.")
        self.current_server_state['time'] = datetime.datetime.now().isoformat()
        for key in log_dict.keys():
            self.current_server_state[step][key] = log_dict[key]
        if not self.validate(self.current_server_state):
            raise DeploymentError("Log data not validate.")
        self.log_collection.insert_one({}, self.current_server_state)

    def validate(self, data):
        try:
            validate(data, self.schema)
        except ValidationError:
            return False
        return True
