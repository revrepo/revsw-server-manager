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
            {'status': {'sjc': {'status': 'down', 'since': 1513890023,
                                  'fail_set': ['Failure for Rule: output contains this is a test',
                                                'Connection error/Timeout']},
                         'global': {'status': 'up', 'since': 1513890023, 'fail_set': ['sjc']}},
             'notify_list': None, 'notify_repeat': 0, 'notify_failback': True, 'name': 'test-test1.host',
             'mute': False, 'rules': [{'comparison': 'contains', 'key': 'output', 'value': 'this is a test'}],
             'notes': None, 'notify_delay': 0, 'job_type': 'tcp', 'notify_regional': False, 'regions': ['sjc'],
             'active': True, 'v2': True, 'frequency': 60, 'rapid_recheck': False, 'policy': 'quorum',
             'region_scope': 'fixed',
             'config': {'response_timeout': 1000, 'host': 'test-test1.host', 'connect_timeout': 2000,
                         'send': 'GET /test-cache.js HTTP/1.1\nHost: monitor.revsw.net\n\n', 'port': 80},
             'id': '1234'}
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
                "send": "GET /test-cache.js HTTP/1.1\nHost: monitor.revsw.net\n\n"
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




