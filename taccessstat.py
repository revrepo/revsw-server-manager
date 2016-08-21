#!/usr/bin/python
"""
	Extermly simple taccess parser to count the number of lines per second.
"""
import threading
import sys
import subprocess
import time
import re
import signal
import os

TACCESS_TOOL = "taccess 2> /dev/null"
INTERVAL = 1
RPS = 0
OUT = 0
KEEP_WORKING = True

re_apache_log_tokens = re.compile('\"(.*?)\"|\[(.*?)\]|(\S+)')
    
def log_loop():
	""" Read log events and update stats """
	global RPS,OUT,KEEP_WORKING,taccess_pid
	try:
		taccess_proc = subprocess.Popen([TACCESS_TOOL], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
		taccess_pid = taccess_proc.pid
		while KEEP_WORKING:
			log_line = taccess_proc.stdout.readline()
			if len(log_line) == 0:
				""" Tail killed by ctrl-c """
				KEEP_WORKING = False
				break
			try:
				line_list = map(''.join, re_apache_log_tokens.findall(log_line))
				out_traffic = int(line_list[7])
				status_code = int(line_list[6]) 
				RPS += 1
				OUT += out_traffic
			except IndexError:
				""" Cutted lines due to log rotation and tail """
				pass
	except (KeyboardInterrupt, SystemExit):
		KEEP_WORKING = False

def print_loop(count=None):
	""" Print log events """
	global RPS,OUT,KEEP_WORKING,taccess_pid
	
	RPS = 0
	OUT = 0
	try:
		while KEEP_WORKING:
			time.sleep(INTERVAL)
			""" Just a quick fix to not print broken lines, if the reading process broke """
			if not KEEP_WORKING:
				break
			print "RPS: %d OUT: %d" % (int(RPS / INTERVAL), int(OUT / INTERVAL))
			RPS = 0
			OUT = 0
			if count is not None:
				count -= 1
				if count <= 0:
					KEEP_WORKING = False
					if taccess_pid > 0:
						os.kill(taccess_pid, 9)
					break
					
	except (KeyboardInterrupt, SystemExit):
		KEEP_WORKING = False
			
if __name__ == "__main__":
	""" Check root """
	if not os.geteuid()==0:
		sys.exit("\nMust be root\n")

	try:
		count = int(sys.argv[1])
	except:
		count = None
		
	""" Start log and print loops """
	log_loop_thread = threading.Thread(target=log_loop)
	log_loop_thread.daemon = True
	print_loop_thread = threading.Thread(target=print_loop, args=(count,))
	print_loop_thread.daemon = True
	log_loop_thread.start()
	print_loop_thread.start()
	
	try:
		print_loop_thread.join()
		log_loop_thread.join()
	except (KeyboardInterrupt, SystemExit):
		KEEP_WORKING = False
