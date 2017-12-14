# NAGIOS CREDENTIALS
import os

NAGIOS_URL = "http://iad02-monitor01.revsw.net:8081/"

# NSONE CREDENTIALS
NSONE_API_KEY = 'LYvs2DdEm3rI8IdX0wuj'

# Server Naming
DEFAULT_DOMAIN = "REVSW.NET"

# Default upgrade command
UPGRADE_COMMAND = "sudo sh /opt/revsw-config/scripts/upgrade.sh"

# Default test command
PROXY_TEST_COMMAND = "sudo sh /opt/revsw-config/scripts/test.sh"

# Default SSH timeout in seconds
SSH_CONNECT_TIMEOUT_SECONDS = 30

# Logging config
LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)-5s %(module)-6s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'RS': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'paramiko.transport': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'Server': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'Dyn': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'NSOne': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'Nagios': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}


MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_DB_NAME = "logging_db"

INFRADB_URL = 'https://testsjc20-manager01.revsw.net/api/'
INFRADB_USERNAME = 'apiuser'
INFRADB_PASSWORD = "FjyWcSpBSP29MXhC"

NSONE_KEY = "0mSdz88RzfIElZRshilB"
NS1_DATA_SOURCE_ID = "c53f31f5e1817442d16b3eaac813a644"

CDS_URL = 'https://testsjc20-cds02.revsw.net:9000/'
CDS_API_KEY = 'sdtq34tqsdfasfdsdKJHIJHKJH656HGFhfyhgf'

SSL_CONF_MONITORING_TIME = 5
WAF_SDK_MONITORING_TIME = 10
DOMAIN_PURGE_MONITORING_TIME = 10

INSTALL_SERVER_HOST = "TESTSJC20-INSTALL01.revsw.net"
INSTALL_SERVER_LOGIN = "sergey"
INSTALL_SERVER_PASSWORD = ""

PUPET_LINKS = {
    "14.04": "http://apt.puppetlabs.com/puppetlabs-release-trusty.deb",
    "16.04": "http://apt.puppetlabs.com/puppet-release-xenial.deb"

}
PUPPET_SERVER = "TESTSJC20-INSTALL01.REVSW.NET"

NAGIOS_SERVER = "TESTSJC02-MONITOR01.REVSW.NET"
NAGIOS_SERVER_LOGIN = "sergey"
NAGIOS_SERVER_PASSWORD = ""
NAGIOS_CFG_PATH = "/etc/nagios/objects/server-manager"

CACTI_SERVER = "TESTSJC02-MONITOR01.REVSW.NET"
CACTI_SERVER_LOGIN = "sergey"
CACTI_SERVER_PASSWORD = ""

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

try:
    import local_settings

except ImportError:
    pass