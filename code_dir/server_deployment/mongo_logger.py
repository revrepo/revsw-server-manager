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

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import settings
from server_deployment.utilites import DeploymentError


class MongoLogger():

    schema = {
        "type": "object",
        "properties": {
            "time": {"type": "string"},
            "start_time": {"type": "string"},
            "host": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string"},
                    "ipv4": {"type": "string", "pattern": "(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"},
                    "ipv6": {"type": "string", "pattern": "(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"},
                    "login": {"type": "string"},
                    "password": {"type": "string"},
                    "cert": {"type": "string"},
                    "reboot": {"type": "string", "pattern": "yes|no|fail"},
                    "ping": {"type": "string", "pattern": "yes|no|fail"},
                    "udp_port_list": {"type": "array", "items": {"type": "string", "pattern": '^([0-9]{1,4})$'}}, # comma/space separated list or range x-xxxxx
                    "tcp_port_list": {"type": "array", "items": {"type": "string", "pattern": '^([0-9]{1,4})$'}}, # comma/space separated list or range x-xxxxx
                    "puppet_installed": {"type": "string", "pattern": "yes|no|fail"},
                    "puppet_configured": {"type": "string", "pattern": "yes|no|fail"},
                    "nagios_installed": {"type": "string", "pattern": "yes|no|fail"},
                    "nagios_configured": {"type": "string", "pattern": "yes|no|fail"},
                    "cacti_installed": {"type": "string", "pattern": "yes|no|fail"},
                    "cacti_configured": {"type": "string", "pattern": "yes|no|fail"},
                    "update": {"type": "string", "pattern": "yes|no|fail"},
                    "upgrade": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"} # [|if returned code !=0]
                },
            },
            "hoster": {
                "type": "object",
                "properties": {
                    "api": {"type": "string", "pattern": "yes|no|fail"},
                    "fw": {"type": "string"}, # [off|proper_set]
                    "udp_port_list": {"type": "array", "items": {"type": "string", "pattern": '^([0-9]{1,4})$'}}, # comma/space separated list or range x-xxxxx
                    "tcp_port_list": {"type": "array", "items": {"type": "string", "pattern": '^([0-9]{1,4})$'}}, # comma/space separated list or range x-xxxxx
                    "log": {"type": "string"} # [|if some fail]
                }
            },
            "ns1": {
                "type": "object",
                "properties": {
                    "host_added": {"type": "string", "pattern": "yes|no|fail"},
                    "monitored": {"type": "string", "pattern": "yes|no|fail"},
                    "monitor_type": {"type": "string", "pattern": "tcp|dns|ping|http"},
                    "port": {"type": "string",}, # for tcp
                    "log": {"type": "string"} # [|if some fail]
                }
            },
            "infraDB": {
                "type": "object",
                "properties": {
                    "server_add":  {"type": "string", "pattern": "ok|no|fail"},
                    "fw":  {"type": "string", "pattern": "ok|no|fail"},
                    "log": {"type": "string"} # [|if some fail]
                }

            },
            "revsw": {
                "type": "object",
                "properties": {
                    "revws_repo":   {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"} # [|if some fail]
               }
            },
            "nagios": {
                "type": "object",
                "properties": {
                    "nagios_conf":   {"type": "string", "pattern": "yes|no|fail"},
                    "nagios_reload": {"type": "string", "pattern": "yes|no|fail"},
                    "log": {"type": "string"} # [|if some fail]
               }
            }
        },
        "required": [
            "time", "start_time", "host", "hoster", "revsw", "infraDB", "nsone"
        ]
    }

    def __init__(self, host_name, start_time):
        self.mongo_cli = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]
        self.log_collection = self.mongo_db[host_name]
        self.current_server_state = {
            "start_time": start_time,
            "time": None,
            "host": {},
            "hoster": {
                "api": 'no',
                "fw": 'off',
            },
            "ns1": {
                "host_added": 'no',
                "monitored": 'no',
            },
            "infraDB": {
                "fw": 'no',
            },
            "revsw": {
                "revws_repo":   'no',
            }
        }

    def log(self, log_dict, step):
        pass
        # if step not in self.current_server_state.keys():
        #     raise DeploymentError("Wrong logging keys.")
        # self.current_server_state['time'] = datetime.datetime.now().isoformat()
        # self.current_server_state[step] = log_dict
        # if not self.validate(self.current_server_state):
        #     raise DeploymentError("Log data not validate.")
        # self.log_collection.insert_one(self.current_server_state)

    def validate(self, data):
        try:
            validate(data, self.schema)
        except ValidationError:
            return False
        return True
