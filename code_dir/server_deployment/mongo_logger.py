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

    def __init__(self, host_name, start_time, initial_data, logger_schema, initial_state, steps):
        self.mongo_cli = pymongo.MongoClient(
            settings.MONGO_HOST, settings.MONGO_PORT
        )
        self.mongo_db = self.mongo_cli[settings.MONGO_DB_NAME]

        self.log_collection = self.mongo_db[host_name]
        self.log_collection.ensure_index('notification',sparse=True)
        self.current_server_state = initial_state
        self.current_server_state['start_time'] = start_time
        self.current_server_state['initial_data'] = initial_data
        # self.log_collection.insert_one(self.current_server_state)
        self.steps = steps
        self.schema = logger_schema
        self.current_step = None

    def log(self, log_dict):
        if self.current_step not in self.current_server_state.keys():
            raise DeploymentError("Wrong logging keys.")
        self.current_server_state['time'] = datetime.datetime.now().isoformat()
        for key in log_dict.keys():
            self.current_server_state[self.current_step][key] = log_dict[key]
        if not self.validate(self.current_server_state):
            raise DeploymentError("Log data not validate.")
        self.log_collection.delete_one({})
        self.log_collection.insert(self.current_server_state)

    def validate(self, data):
        try:
            validate(data, self.schema)
        except ValidationError:
            return False
        return True

    def init_new_step(self, step_name):
        if step_name not in self.steps:
            raise DeploymentError("Wrong step name")
        self.current_step = step_name
        self.current_server_state[self.current_step]['log'] = ''
        self.log({'runned': "yes"})

    def add_logs(self, log_entry):
        self.current_server_state[self.current_step]['log'] += log_entry
        self.log_collection.delete_one({})
        self.log_collection.insert(self.current_server_state)
