from server import Server
from nsone import Nsone
from pprint import pprint 
import re
import time
import subprocess
import settings

re_taccessstat = re.compile("RPS: (\d+) OUT: (\d+)") 


class Proxy(Server):
    def suspend(self):
        self.info("Suspending.")
        
        self.info("nsone, fail monitoring job.")
        nsone = Nsone()
        nsone.fail_monitoring_job(self.server_name)            

    def resume(self):
        self.info("Resuming.")
        
        self.info("nsone, unfail monitoring job.")
        nsone = Nsone()
        nsone.unfail_monitoring_job(self.server_name)            
    
    def upgrade(self):
        # self.nagios_schedule_downtime()
        self.suspend()
        self.wait_low_traffic()
        self.force_upgrade()
        self.test()
        self.resume()
        # self.nagios_cancel_downtime()
        
    def force_upgrade(self):
        self.info("Running upgrade script.")
        out, err, status = self.command(settings.UPGRADE_COMMAND)
        self.debug("Upgrade script exit status: %d" % status)
        if len(out) == 0:
            self.debug("No upgrade script output.")
        else:
            self.debug("upgrade script out:\n%s\n" % out)
            
        if len(err) == 0:
            self.debug("No upgrade script error messages.")
        else:
            self.debug("upgrade script err:\n%s\n" % err)
            
        if status != 0:
            err_msg = "Failed running upgrade command.\nCODE: %d\nOUT:\n%s\nERR:\n%s\n" % ( status,out,err) 
            self.fatal(err_msg)
            raise Exception(err_msg)            
        
    def test(self):
        self.info("Running proxy test script")
        out, err, status = self.command(settings.PROXY_TEST_COMMAND)

        self.debug("Test script exit status: %d" % status)
        if len(out) == 0:
            self.debug("No test script output.")
        else:
            self.debug("test script out:\n%s\n" % out)

        if len(err) == 0:
            self.debug("No test script error messages.")
        else:
            self.debug("test script err:\n%s\n" % err)

        if status != 0:
            err_msg = "Failed running test command.\nCODE: %d\nOUT:\n%s\nERR:\n%s\n" % (status, out, err)
            self.fatal(err_msg)
            raise Exception(err_msg)

    def check_traffic(self):
        self.info("Checking traffic.")
        out, err, status = self.command("sudo /usr/local/sbin/taccessstat.py 30")
        if status != 0:
            err_msg = "Failing getting traffic figures from server."
            self.fatal(err_msg)
            raise Exception(err_msg)
        """ Skip first line,as it got history, split thre rest """
        samples = out.split("\n")[1:-1]
        count = 0
        total_rps = 0
        total_out = 0
        for s in samples:
            count += 1
            m = re_taccessstat.match(s).group(1,2)
            (rps, out) = re_taccessstat.match(s).group(1,2)
            rps = int(rps)
            out = int(out)
            total_rps += rps
            total_out += out
            
        return int(total_rps/count), int(total_out/count)
    
    def wait_low_traffic(self):
        self.info("Waiting for low traffic.")
        max_rps = 1
        sleep_time = 10
        while True:
            rps, out = self.check_traffic()
            if rps > max_rps:
                self.info("Still at %d rps, waiting for %d rps. Will sleep now for %d seconds." % (rps, max_rps, sleep_time))
                time.sleep(sleep_time)
            else:
                self.info("Traffic is low.")
                return True

#     def track_traffic(self):
#         for l in self.streamline_command("sudo /usr/local/sbin/taccessstat.py"):
#             print "l: %s" % l
# 
#     def test_track(self):
#         for l in self.streamline_command("bash -i -c -l \"sudo ~moty/test.py\""):
#             print "l: %s" % l
#     
    
if __name__ == "__main__":
    p = Proxy("PAR02-BP01.REVSW.NET")
    p.test_track()
