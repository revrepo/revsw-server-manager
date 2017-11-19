
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

from server_deployment.mongo_logger import MongoLogger
from server_deployment.server_state import ServerState
from server_deployment.utilites import DeploymentError

if __name__ == "__main__":
    try:
        # TODO: here will be main sequence of server deploy
        pass
    except DeploymentError as e:
        pass
