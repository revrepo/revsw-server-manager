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

from nsone.rest.errors import ResourceException

import settings


class MockNSONE():

    success = True  # flag to force functions work correctly or give exeption

    def __init__(self, apikey):
        self.apikey = apikey
        self.monitor = NS1MonitorMock()

    def loadZone(self):
        return NS1ZoneMock()


class NS1MonitorMock():
    success = True  # flag to force functions work correctly or give exeption

    monitor_list = [
            {
                'status': {
                    'sjc': {
                        'status': 'down',
                        'since': 1513890023,
                        'fail_set': [
                            'Failure for Rule: output contains this is a test',
                            'Connection error/Timeout'
                        ]
                    },
                    'global': {
                        'status': 'up',
                        'since': 1513890023,
                        'fail_set': ['sjc']
                    }
                },
                'notify_list': None,
                'notify_repeat': 0,
                'notify_failback': True,
                'name': 'test-test1.host',
                'mute': False,
                'rules': [
                    {
                        'comparison': 'contains',
                        'key': 'output',
                        'value': 'this is a test'
                    }
                ],
                'notes': None,
                'notify_delay': 0,
                'job_type': 'tcp',
                'notify_regional': False,
                'regions': ['sjc'],
                'active': True,
                'v2': True,
                'frequency': 60,
                'rapid_recheck': False,
                'policy': 'quorum',
                'region_scope': 'fixed',
                'config': {
                    'response_timeout': 1000,
                    'host': 'test-test1.host',
                    'connect_timeout': 2000,
                    'send': 'GET /test-cache.js HTTP/1.1\nHost:'
                            ' monitor.revsw.net\n\n',
                    'port': 80
                },
                'id': '1234'
            }
        ]

    def list(self):
        return self.monitor_list

    def create(self, monitor_data):
        # checking data
        example_data = {
            "region_scope": "fixed",
            "frequency": 20,
            "rapid_recheck": False,
            "policy": "quorum",
            "notify_delay": 0,
            "notify_repeat": 0,
            "notify_failback": True,
            "notify_regional": False,
            "rules": [
                {
                    "key": "output",
                    "comparison": "contains",
                    "value": "this is a test"}
            ],
            "regions": ["sjc", "sin", "lga"],
            "job_type": "tcp",
            "config": {
                "response_timeout": 1000,
                "connect_timeout": 2000,
                "host": 'test-test2.host',
                "port": 80,
                "send": "GET /test-cache.js HTTP/1.1\nHost: "
                        "monitor.revsw.net\n\n"
            },
            "name": 'test-test2.host',
            "notify_list": settings.NS1_NOTIFY_LIST_ID
        }
        if example_data != monitor_data:
            raise ResourceException("Data not equals")
        if not self.success:
            raise ResourceException("forced error")
        return '5432'

    def retrieve(self, monitor_id):
        for monitor in self.monitor_list:
            if monitor['id'] == monitor_id:
                return monitor
        raise ResourceException("Monitor not found")

    def delete(self, monitor_id):
        if not self.success:
            raise ResourceException("forced error")
        return True


class NS1ZoneMock():

    def load(self):
        return self

    def add_A(self, name, hosts):
        return


class NS1FeedMock():

    def create(self, source_id, name, config={}):
        return self

    def list(self, source_id):
        return

    def delete(self, source_id, feed_id):
        return


class Objectview(object):
    def __init__(self, d):
        self.__dict__ = d


class MockedInfraDB():

    def __init__(self, *args, **kwargs):
        pass
    called_functions = {}

    def get_server(self, host_name):
        self.called_functions['get_server'] = [host_name, ]

    def add_server(
            self, host_name, ip, server_versions,
                   ):
        self.called_functions['add_server'] = [
            host_name, ip, server_versions
        ]

    def delete_server(self, host_name):
        self.called_functions['delete_server'] = [host_name]


class MockedServerClass():

    def __init__(self, *args, **kwargs):
        pass

class MockedNagiosClass():

    def __init__(self, *args, **kwargs):
        pass

    def check_services_status(self):
        pass


class NS1Record():

    data = {
        "answers": [
            {"answer": ['111.111.111.11',], "id": "1213"}
        ]
    }

    def update(self, *args, **kwargs):
        pass

    def delete(self):
        pass


class MockedExecOutput():


    def __init__(self, output_list, return_status=0):
        self.output_list = output_list
        self.channel = MockedChannel(return_status)

    def readlines(self):
        return self.output_list


class MockedChannel():

    def __init__(self, return_status):
        self.return_status = return_status

    def recv_exit_status(self):
        return self.return_status
