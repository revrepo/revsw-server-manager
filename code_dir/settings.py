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
            'format': '%(levelname)s %(asctime)s %(module)s'
                      ' %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)-5s %(module)-6s %(message)s'
        },
        'timing': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'console_full': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'timing'
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
        'ServerDeploy': {
            'handlers': ['console_full'],
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
NS1_DNS_ZONE_DEFAULT = "attested.club"
NS1_NOTIFY_LIST_ID = "53ab4ad82db15606fd61f1e6"
NS1_MONITOR_WAITING_TIME = 60
NS1_AFTER_ANSWER_DELETING_WAIT_TIME = 60*10
NS1_MINIMAL_ANSWERS_COUNT = 30

CDS_URL = 'https://testsjc20-cds02.revsw.net:9000/'
CDS_API_KEY = 'sdtq34tqsdfasfdsdKJHIJHKJH656HGFhfyhgf'
CDS_WAITING_TIME = 40
SERVER_GROUP = "5588823fbde7a0d00338ce8d"

SSL_CONF_MONITORING_TIME = 5
WAF_SDK_MONITORING_TIME = 10
DOMAIN_PURGE_MONITORING_TIME = 10

INSTALL_SERVER_HOST = "TESTSJC20-INSTALL01.revsw.net"
INSTALL_SERVER_LOGIN = "sergey"
INSTALL_SERVER_PASSWORD = ""

REBOOT_SLEEP_TIME = 30

PUPET_LINKS = {
    "14.04": "http://apt.puppetlabs.com/puppetlabs-release-trusty.deb",
    "16.04": "http://apt.puppetlabs.com/puppet-release-xenial.deb"
}
PUPPET_SERVER = "TESTSJC20-INSTALL01.REVSW.NET"

NAGIOS_SERVER = "TESTSJC02-MONITOR01.REVSW.NET"
NAGIOS_SERVER_LOGIN = "sergey"
NAGIOS_SERVER_PASSWORD = ""
NAGIOS_CFG_PATH = "/etc/nagios/objects/server-manager"
NAGIOS_TEMP_CFG_PATH = "/tmp"
NAGIOS_FORCING_CHECK_SERVICES_WAIT_TIME = 60

IGNORE_NAGIOS_SERVICES = ["NTP Status", "Net: Traffic on eth0"]

CACTI_SERVER = "TESTSJC02-MONITOR01.REVSW.NET"
CACTI_SERVER_LOGIN = "sergey"
CACTI_SERVER_PASSWORD = ""

BASE_DIR = os.path.dirname(__file__)

DEFAULT_USERNAME = 'robot'
DEFAULT_PASSWORD = '12345678'

KEY_PATH = os.path.join(BASE_DIR, 'keys/id_rsa')

REQUIRED_RAM_SIZE = 2048  # in MB
REQUIRED_FREE_SPACE = 30 * 1024  # in MB
REQUIRED_SYSTEM_VERSION = '14.04'
REQUIRED_HW_ARCHITECTURE = "x86_64"

PSSH_SERVER = "IAD02-MANAGER01.REVSW.NET"
PSSH_SERVER_LOGIN = "sergey"
PSSH_SERVER_PASSWORD = ""
PSSH_FILE_PATH = "/home/victor/pssh/all-bp"


try:
    from local_settings import *

except ImportError:
    pass