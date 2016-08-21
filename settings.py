# NAGIOS CREDENTIALS
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
