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
from logging import Handler


class DeploymentError(Exception):
    """Exception raised for errors which was raised while deployment.
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class MongoDBHandler(Handler):
    mongo_log = None

    def add_mongo_logger(self, logger):
        self.mongo_log = logger

    def emit(self, record):
        log_entry = self.format(record)
        if self.mongo_log:
            if record.levelname in ["ERROR", "CRITICAL"]:
                self.mongo_log.log({"error_log": log_entry})
            self.mongo_log.add_logs(log_entry)
