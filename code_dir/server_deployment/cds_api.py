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

import json
import logging
import time
from datetime import datetime
from urlparse import urljoin

import requests

import settings
from server_deployment.utilites import DeploymentError

logger = logging.getLogger('ServerDeploy')
logger.setLevel(logging.DEBUG)


class CDSAPI():

    def __init__(self, server_group_id, server_name, logger):
        self.server_name = server_name
        self.logger = logger
        self.session = requests.Session()
        self.url = settings.CDS_URL
        self.server_group_id = server_group_id
        self.server_group = self._get_server_group()
        self.highest_versions = {
            'ssl': self._get_highest_ssl_version(),
            'sdk': self._get_highest_sdk_version(),
            'domain': self._get_highest_domain_version(),
            'waf': self._get_highest_waf_version(),
            'purge': self._get_highest_purge_version()
        }

    def _get_server_group(self):
        response = requests.get(
            urljoin(self.url, 'v1/server_groups/%s' % self.server_group_id),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            raise DeploymentError(log_error)
        server_group = json.loads(response.content)
        if not server_group:
            log_error = "Server error. Wrong server group name." \
                        " Server group not found"
            raise DeploymentError(log_error)

        if server_group["groupType"] != "BP":
            log_error = "CDS  error. Wrong server group"
            raise DeploymentError(log_error)
        return server_group

    def _get_highest_waf_version(self):
        response = requests.get(
            urljoin(self.url, '/v1/waf_rule_jobs/status'),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        resp = json.loads(response.content)

        return resp["highest_waf_rule_job_id"]

    def _get_highest_ssl_version(self):
        response = requests.get(
            urljoin(self.url, 'v1/ssl_jobs/status'),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        resp = json.loads(response.content)

        return resp["highest_ssl_cert_job_id"]

    def _get_highest_sdk_version(self):
        response = requests.get(
            urljoin(self.url, 'v1/app_jobs/status'),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        resp = json.loads(response.content)

        return resp["highest_app_job_id"]

    def _get_highest_purge_version(self):
        response = requests.get(
            urljoin(self.url, 'v1/purge_jobs/status'),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        resp = json.loads(response.content)

        return resp["highest_purge_job_id"]

    def _get_highest_domain_version(self):
        response = requests.get(
            urljoin(self.url, 'v1/domain_config_jobs/status'),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        resp = json.loads(response.content)

        return resp["highest_domain_config_job_id"]

    def check_server_exist(self):
        logger.info("Check existed server in CDS")
        response = requests.get(
            urljoin(self.url, 'v1/proxy_servers/byname/%s' % self.server_name),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code not in [200, 400]:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"check_server_exist": "fail", "log": log_error})
            raise DeploymentError(log_error)
        resp = json.loads(response.content)
        if response.status_code == 400:
            if resp["message"] == "Server not found":
                return False
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"check_server_exist": "fail", "log": log_error})
            raise DeploymentError(log_error)
        logger.info('Server found with id %s' % resp["_id"])
        self.proxy_server = resp
        return self.proxy_server

    def add_server(self, ip, environment):
        logger.info("Add new server to CDS")
        server_data = {
            "server_name": self.server_name,
            "server_ip": ip,
            "status": "pending",
            "type": "BP",
            "environment": environment,
            "proxy_schema_version": 0,
            "domain_config_version": self.highest_versions['domain'],
            "app_config_version": self.highest_versions['sdk'],
            "purge_version": self.highest_versions['purge'],
            "ssl_cert_version": 0,
            "waf_rule_version": self.highest_versions['waf'],
        }
        response = requests.post(
            urljoin(self.url, '/v1/proxy_servers'),
            data=server_data,
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code not in [200, 201]:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_add": "fail", "error_log": log_error})
            raise DeploymentError(log_error)
        self.proxy_server = json.loads(response.text)
        self.logger.log({"sever_add": "yes"})
        # TODO fix this log
        logger.info("new server id ")

    def update_server(self, update_data):
        response = requests.put(
            urljoin(
                self.url,
                '/v1/proxy_servers/%s' % self.proxy_server['_id']
            ),
            data=update_data,
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code not in [200, 201]:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_add": "fail", "error_log": log_error})
            raise DeploymentError(log_error)
        self.proxy_server = json.loads(response.text)

    def check_installed_packages(self, server):
        logger.info("Checking installed packages for CDS")
        packages = ['revsw-proxy-config', 'revsw-libvarnish4api',
                    'revsw-nginx-common',
                    'revsw-nginx-naxsi', 'Revsw-quic-proxy',
                    'revsw-varnish4-modules',
                    'revsw-varnish4', 'Varnish-mod-wurfl', 'libwurfl'
                    ]
        for pack in packages:
            if not server.check_install_package(pack):
                log_error = "%s not installed" % pack
                self.logger.log(
                    {"check_packages": "fail", "error_log": log_error}
                )
                raise DeploymentError(log_error)
            logger.info("%s installed." % pack)
        self.logger.log({"check_packages": "yes"})

    def monitor_ssl_configuration(self):
        start_time = datetime.now()
        iteration = 0
        logger.info(
            "start monitoring to update ssl "
            "configuration %s" % start_time.isoformat()
        )
        while iteration != (settings.SSL_CONF_MONITORING_TIME*60/10):
            response = requests.get(
                urljoin(
                    self.url, 'v1/proxy_servers/%s' % self.proxy_server['_id']
                ),
                headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
            )
            if response.status_code == 200:
                proxy = json.loads(response.text)
                logger.info("SSL configuration version %s of %s" % (
                    proxy["ssl_cert_version"], self.highest_versions['ssl'])
                            )
                if proxy["ssl_cert_version"] >= self.highest_versions['ssl']:
                    finish_time = datetime.now()
                    logger.info(
                        "end monitoring to update ssl"
                        " configuration %s" % finish_time.isoformat()
                    )
                    self.logger.log(
                        {"install_ssl_configuration": "yes"}
                    )
                    return {
                        'start_time': start_time,
                        "finish_time": finish_time
                    }

            iteration += iteration
            time.sleep(10)
        self.logger.log(
            {
                "install_ssl_configuration": "fail",
                "error_log": "To long installing"
            }
        )
        raise DeploymentError("To long installing")

    def monitor_waf_and_sdk_configuration(self):
        start_time = datetime.now()
        iteration = 0
        logger.info(
            "start monitoring to update waf and sdk "
            "configuration %s" % start_time.isoformat()
        )
        while iteration != (settings.WAF_SDK_MONITORING_TIME*60/10):
            response = requests.get(
                urljoin(
                    self.url, 'v1/proxy_servers/%s' % self.proxy_server['_id']
                ),
                headers={
                    'Authorization': 'Bearer %s' % settings.CDS_API_KEY
                }
            )
            if response.status_code == 200:
                proxy = json.loads(response.text)
                logger.info("waf version %s of %s sdk version %s of %s" % (
                    proxy["waf_rule_version"], self.highest_versions['waf'],
                    proxy["app_config_version"], self.highest_versions['sdk']
                ))
                if proxy["app_config_version"] >= \
                   self.highest_versions['sdk'] and \
                   proxy["waf_rule_version"] >= self.highest_versions['waf']:
                    finish_time = datetime.now()
                    logger.info(
                        "end monitoring to update waf and sdk "
                        "configuration %s" % finish_time.isoformat()
                    )
                    self.logger.log(
                        {"install_waf_and_sdk_configuration": "yes"}
                    )
                    return {
                        'start_time': start_time,
                        "finish_time": finish_time
                    }

            iteration += iteration
            time.sleep(10)
        self.logger.log(
            {
                "install_waf_and_sdk_configuration": "fail",
                "error_log": "To long installing"
            }
        )
        raise DeploymentError("To long installing")

    def monitor_purge_and_domain_configuration(self):
        start_time = datetime.now()
        iteration = 0
        logger.info(
            "start monitoring to update purge and domain"
            " configuration %s" % start_time.isoformat()
        )
        while iteration != (settings.DOMAIN_PURGE_MONITORING_TIME*60/10):
            response = requests.get(
                urljoin(
                    self.url, 'v1/proxy_servers/%s' % self.proxy_server['_id']
                ),
                headers={
                    'Authorization': 'Bearer %s' % settings.CDS_API_KEY
                }
            )
            if response.status_code == 200:
                proxy = json.loads(response.text)
                logger.info(
                    "domain_config version %s of %s "
                    "purge_version version %s of %s" % (
                        proxy["domain_config_version"],
                        self.highest_versions['domain'],
                        proxy["purge_version"],
                        self.highest_versions['purge']
                    )
                )

                if proxy["domain_config_version"] >=\
                   self.highest_versions['domain'] and \
                   proxy["purge_version"] >= self.highest_versions['purge']:
                    finish_time = datetime.now()
                    logger.info(
                        "end monitoring to update purge and domain "
                        "configuration %s" % finish_time.isoformat())
                    self.logger.log(
                        {"install_purge_and_domain_configuration": "fail"}
                    )
                    return {
                        'start_time': start_time,
                        "finish_time": finish_time
                    }
            iteration += iteration
            time.sleep(10)
        self.logger.log(
            {
                "install_purge_and_domain_configuration": "fail",
                "error_log": "To long installing"
            }
        )
        raise DeploymentError("To long installing")

    def add_server_to_group(self):
        logger.info("adding server to group")
        new_servers = '%s,%s' % (
            self.server_name, self.server_group['servers']
        )
        response = requests.put(
            urljoin(
                self.url,
                '/v1/server_groups/%s' % self.server_group['_id']
            ),
            data={'servers': new_servers},
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code not in [200, 201]:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_add": "fail", "log": log_error})
            raise DeploymentError(log_error)
        logger.info("server succesful added to group")
        self.server_group = json.loads(response.text)
        logger.info(self.server_group)

    def delete_server(self):
        logger.info("Delete server from CDS")
        response = requests.delete(
            urljoin(
                self.url,
                '/v1/proxy_servers/%s' % self.proxy_server['_id']
            ),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code not in [200, 201]:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_add": "fail", "log": log_error})
            raise DeploymentError(log_error)

    def get_all_group_with_this_server(self):

        response = requests.get(
            urljoin(self.url, '/v1/server_groups'),
            headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
        )
        if response.status_code != 200:
            log_error = "Server error. Status: %s Error: %s" % (
                response.status_code, response.text
            )
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        server_groups = json.loads(response.content)
        if not server_groups:
            log_error = "Server error. Wrong hosting provider name." \
                        " Hosting provider not found"
            self.logger.log({"sever_group": "fail", "log": log_error})
            raise DeploymentError(log_error)
        group_with_server = []
        for group in server_groups:
            if self.server_name in group['servers']:
                group_with_server.append(group)
        return group_with_server

    def delete_server_from_groups(self):
        group_list = self.get_all_group_with_this_server()
        for group in group_list:
            logger.info("delete server from group %s" % group['_id'])
            servers_list = group['servers'].split(',')
            servers_list.remove(self.server_name)
            response = requests.put(
                urljoin(self.url, '/v1/server_groups/%s' % group['_id']),
                data={'servers': ",".join(servers_list)},
                headers={'Authorization': 'Bearer %s' % settings.CDS_API_KEY}
            )
            if response.status_code not in [200, 201]:
                log_error = "Server error. Status: %s Error: %s" % (
                    response.status_code, response.text
                )
                self.logger.log({"sever_add": "fail", "log": log_error})
                raise DeploymentError(log_error)

    def check_server_in_group(self):
        return self.server_name in self.server_group['servers']

    def check_need_update_versions(self):
        check_list = {
            'ssl': False,
            'waf_sdk': False,
            'domain_purge': False
        }

        if self.highest_versions['ssl'] > \
           self.proxy_server["ssl_cert_version"]:
            check_list['ssl'] = True
        if self.highest_versions['sdk'] > \
           self.proxy_server["app_config_version"] or \
           self.highest_versions['waf'] > \
           self.proxy_server["waf_rule_version"]:
            check_list['waf_sdk'] = True
        if self.highest_versions['domain'] >\
           self.proxy_server["domain_config_version"] or \
           self.highest_versions['purge'] > self.proxy_server["purge_version"]:
            check_list['domain_purge'] = True
        return check_list
