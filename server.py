import paramiko.client
import paramiko
from time import sleep
import select
import sys
import settings
import logging
from nagios import Nagios

logger = logging.getLogger('Server')
logger.setLevel(logging.DEBUG)


class Server(object):
    
    def debug(self,msg):
        logger.debug("%s: %s" % (self.server_name, msg))

    def info(self,msg):
        logger.info("%s: %s" % (self.server_name, msg))
    
    def error(self,msg):
        logger.error("%s: %s" % (self.server_name, msg))

    def fatal(self,msg):
        logger.fatal("%s: %s" % (self.server_name, msg))
    
    def __init__(self,server_name):
        server_name = server_name.upper()
        if not server_name.endswith(".%s" % settings.DEFAULT_DOMAIN):
            server_name = "%s.%s" % (server_name, settings.DEFAULT_DOMAIN)
            
        self.server_name = server_name
        self.nagios_name = server_name.split(".")[0]
        
        self.debug("Server class initilized.")
#         self.channels = list()
        self.connect()
    
#     def __del__(self):
#         for channel in self.channels:
#             print "Closing some channel"
#             channel.shutdown(2)
    
    def nagios_schedule_downtime(self):
        nagios = Nagios()
        nagios.schedule_downtime(self.nagios_name)
    
    def nagios_cancel_downtime(self):
        nagios = Nagios()
        nagios.cancel_downtime(self.nagios_name)
    
    def connect(self):
        self.ssh = paramiko.client.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.server_name, timeout=settings.SSH_CONNECT_TIMEOUT_SECONDS)
        self.debug("SSH connected.")
#     def get_channel(self):
#         transport = self.ssh.get_transport()
#         channel = transport.open_session()
#         channel.get_pty()
#         self.channels.append(channel)
#         return channel
#         
#     def streamline_command(self,command):
#         channel = self.get_channel()
#         channel.exec_command(command)
#         previous_out = str()
#         while True:
#             rl, wl, xl = select.select([channel],[],[],0.0)
#             if len(rl) > 0:
#                 # Must be stdout
#                 out = channel.recv(1024)
#                 if len(out) == 0:
#                     """ End of command execution """
#                     if len(previous_out) > 0:
#                         yield(previous_out)
#                     return
#                 else:
#                     """ Got output from server, stream out buffer line by line until can't find an end of a line """
#                     out = previous_out + out
#                     try:
#                         while True:
#                             idx = out.index("\n")
#                             yield(out[0:idx]) 
#                             out = out[idx+1:]
#                     except ValueError:
#                         """ Cutted line, needs more input from server """
#                         previous_out = out

    def upload_file(self, local_name, remote_name):
        self.info("Uploading %s to %s:%s" % (local_name, self.server_name, remote_name))
        local_file = open(local_name, "r")
        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        sftp.put(local_name, remote_name)
        local_file.close()
        
    def command(self,command):
        self.debug("Executing command \"%s\"." % command)
        """ Setup channel and execute command """
        transport = self.ssh.get_transport()
        channel = transport.open_session()
        channel.set_combine_stderr(0)
        channel.setblocking(0)
        channel.exec_command(command)
        
        """ Get output """
        response_out = str()
        response_err = str()
        response_status = None

        while True:
            """ Pause until data is avaiable """
            rl, wl, xl = select.select([channel],[],[],0.0)

            """ Intermidiate data reading, for clearing buffer while the command still runs """
            
            """ STDOUT """
            while channel.recv_ready():
                response_out += channel.recv(1024)
                
            """ STDERR """
            while channel.recv_stderr_ready():
                response_err += channel.recv_stderr(1024)
            
            """ If command finished, set blocking and read the rest of the output """
            if channel.exit_status_ready():
                response_status = channel.recv_exit_status()
                channel.setblocking(1)

                """ STDOUT """
                while True:
                    new_out = channel.recv(1024)
                    if len(new_out) == 0:
                        break
                    response_out += new_out                    

                """ STDERR """
                while True:
                    new_err = channel.recv_stderr(1024)
                    if len(new_err) == 0:
                        break
                    response_err += new_err                    
                
                """ Return out, err, and status code """
                return (response_out, response_err, response_status)
            
if __name__ == "__main__":
    s = Server("localhost")
    out, err, code = s.command("cat /tmp/somefile")
#     print "Out:\n%s" % out
#     print "Err:\n%s" % err
#     print "Code:%d" % code
    sys.stdout.write(out)