#! /usr/bin/python

# Copyright 2016 National Instruments
# This server emulates the NI Service Locator and the NI System Web Server
# Primarily the purpose of this emaulator is to publish a web service to
# reboot the target from the LabVIEW project.

import BaseHTTPServer
from SocketServer import ThreadingMixIn
import urlparse
import os
import socket
import threading
import time
import subprocess

HOST_NAME = ''
PORT_NUMBER = 3580

RESTART_MAX_RETRIES = 3
RESTART_RETRY_DELAY = 1

# Large string constants for XML responses
SYSAPI_RESPONSE_LOGIN = "<?xml version='1.0' encoding='UTF-8'?><Permissions><Permission><Name>GetDB</Name><BuiltIn>false</BuiltIn><ID>0</ID></Permission><Permission><Name>SetDB</Name><BuiltIn>false</BuiltIn><ID>1</ID></Permission><Permission><Name>FSRead</Name><BuiltIn>false</BuiltIn><ID>2</ID></Permission><Permission><Name>FSWrite</Name><BuiltIn>false</BuiltIn><ID>3</ID></Permission><Permission><Name>SSLAdminModifyCerts</Name><BuiltIn>false</BuiltIn><ID>4</ID></Permission><Permission><Name>SSLAdminReadCerts</Name><BuiltIn>false</BuiltIn><ID>5</ID></Permission><Permission><Name>NIWebCer</Name><BuiltIn>false</BuiltIn><ID>6</ID></Permission><Permission><Name>GetWSAPIKey</Name><BuiltIn>false</BuiltIn><ID>7</ID></Permission><Permission><Name>ManageWS</Name><BuiltIn>false</BuiltIn><ID>8</ID></Permission><Permission><Name>SetWSAPIKey</Name><BuiltIn>false</BuiltIn><ID>9</ID></Permission><Permission><Name>WIFConfigureAppServer</Name><BuiltIn>false</BuiltIn><ID>10</ID></Permission><Permission><Name>GetSystemConfiguration</Name><BuiltIn>false</BuiltIn><ID>11</ID></Permission><Permission><Name>SetSystemConfiguration</Name><BuiltIn>false</BuiltIn><ID>12</ID></Permission><Permission><Name>FirmwareUpdate</Name><BuiltIn>false</BuiltIn><ID>13</ID></Permission><Permission><Name>Reboot</Name><BuiltIn>false</BuiltIn><ID>14</ID></Permission><Permission><Name>RemoteShell</Name><BuiltIn>false</BuiltIn><ID>15</ID></Permission><Permission><Name>SetRTLockPassword</Name><BuiltIn>false</BuiltIn><ID>16</ID></Permission><Permission><Name>ViewConsoleOutput</Name><BuiltIn>false</BuiltIn><ID>17</ID></Permission><Permission><Name>GetSyslog</Name><BuiltIn>false</BuiltIn><ID>18</ID></Permission><Permission><Name>ManageExtensions</Name><BuiltIn>false</BuiltIn><ID>19</ID></Permission></Permissions>"

SYSAPI_RESPONSE_ENUM_EXPERTS = "<?xml version='1.0' encoding='utf-8' ?><NISysAPI_Results hr='0' version='00010001'><SystemExperts><ExpertInfo productID='{722D1D51-1C1D-42FE-AEEF-5CF6C711FFA7}' productDisplayName='NI System Configuration' productVersion='21.0.0d101' programmaticName='nisyscfg' /><ExpertInfo productID='{B831EF1F-BF94-42D7-9515-94A1D45F0E41}' productDisplayName='NI Systems Management' productVersion='21.1.0d492' programmaticName='nisysmgmt' /></SystemExperts></NISysAPI_Results>"

SYSAPI_RESPONSE_SEARCH_PROPERTIES = "<?xml version='1.0' encoding='utf-8' ?><NISysAPI_Results hr='0' version='00010001'><PropertyBags><PropertyBag><Property tag='1000000' type='6'>//localhost/nisyscfg/eth0</Property><Property tag='1001000' type='1'>0</Property><Property tag='1009000' type='1'>0</Property><Property tag='100D000' type='3'>0</Property><Property tag='101C000' type='2'>1</Property><Property tag='101D000' type='6'>eth0</Property><Property tag='101E000' type='6'>nisyscfg</Property><Property tag='101F000' type='6'>Ethernet Adapter eth0</Property><Property tag='1020000' type='1'>0</Property><Property tag='1022000' type='5'>{00000000-0000-0000-0000-000000000000}</Property><Property tag='1028000' type='1'>0</Property><Property tag='102A000' type='2'>1000</Property><Property tag='1037000' type='3'>1376256</Property><Property tag='1038000' type='1'>1</Property><Property tag='1039000' type='2'>1</Property><Property tag='103A000' type='3'>5</Property><Property tag='1054000' type='1'>0</Property><Property tag='D102000' type='3'>2</Property><Property tag='D103000' type='3'>2</Property><Property tag='D104000' type='6'>08:00:27:4B:05:76</Property><Property tag='D105000' type='3'>2</Property><Property tag='D106000' type='3'>15</Property><Property tag='D107000' type='6'>%s</Property><Property tag='D108000' type='3'>1</Property><Property tag='D109000' type='6'>255.255.255.0</Property><Property tag='D10A000' type='6'>10.0.62.1</Property><Property tag='D10B000' type='6'>172.18.18.80</Property><Property tag='D10F000' type='3'>1</Property><Property tag='D110000' type='3'>95</Property><Property tag='D111000' type='3'>64</Property><Property tag='D119000' type='3'>1</Property><Property tag='D11A000' type='3'>1</Property><Property tag='D126000' type='1'>1</Property><Property tag='D12C000' type='3'>1</Property></PropertyBag><PropertyBag><Property tag='1000000' type='6'>//localhost/nisyscfg,nisysmgmt/system,system</Property><Property tag='1001000' type='1'>1</Property><Property tag='1002000' type='3'>0</Property><Property tag='1004000' type='6'>National Instruments</Property><Property tag='1005000' type='3'>30517</Property><Property tag='1006000' type='6'>cRIO-903x-VM</Property><Property tag='1007000' type='6'>274B0576</Property><Property tag='1008000' type='1'>1</Property><Property tag='1009000' type='1'>0</Property><Property tag='100D000' type='3'>0</Property><Property tag='101C000' type='2'>2</Property><Property tag='101D000' type='6'>system</Property><Property tag='101D001' type='6'>system</Property><Property tag='101E000' type='6'>nisyscfg</Property><Property tag='101E001' type='6'>nisysmgmt</Property><Property tag='101F000' type='6'>%s</Property><Property tag='101F001' type='6'/><Property tag='1020000' type='1'>0</Property><Property tag='1022000' type='5'>{00000000-0000-0000-0000-000000000000}</Property><Property tag='1022001' type='5'>{DF2FE68E-F8DC-41AE-803C-75BD42785709}</Property><Property tag='1024000' type='2'>1</Property><Property tag='1028000' type='1'>0</Property><Property tag='102A000' type='2'>1000</Property><Property tag='102A001' type='2'>-10000</Property><Property tag='102F000' type='6'>8.8.0d39</Property><Property tag='1033000' type='6'>08:00:27:4B:05:76</Property><Property tag='1037000' type='3'>1376256</Property><Property tag='1037001' type='3'>1376256</Property><Property tag='1038000' type='1'>1</Property><Property tag='1039000' type='2'>1</Property><Property tag='103A000' type='3'>4</Property><Property tag='103C000' type='6'>cRIO</Property><Property tag='103D000' type='6'/><Property tag='104A000' type='1'>1</Property><Property tag='104B000' type='6'>*.cfg</Property><Property tag='104C000' type='2'>0</Property><Property tag='104E000' type='6'>NI-Linux x64</Property><Property tag='104F000' type='6'>4.14.146-rt67</Property><Property tag='1050000' type='6'>NI Linux Real-Time x64 4.14.146-rt67</Property><Property tag='1051000' type='7'>A9775000 B6165EA6 DD163B4A 0</Property><Property tag='1052000' type='1'>0</Property><Property tag='1053000' type='6'>Running</Property><Property tag='1054000' type='1'>0</Property><Property tag='1054001' type='1'>0</Property><Property tag='1058000' type='2'>1</Property><Property tag='1075000' type='6'/><Property tag='1083000' type='6'>Intel(R) Xeon(R) CPU E5-1650 v3 @ 3.50GHz</Property><Property tag='1084000' type='2'>2</Property><Property tag='10B2000' type='2'>1</Property><Property tag='5105000' type='1'>0</Property><Property tag='D11D000' type='6'>en</Property><Property tag='D11E000' type='6'>en</Property><Property tag='D120000' type='6'>CUT0</Property><Property tag='D122000' type='4'>10047024.000000</Property><Property tag='D123000' type='4'>9276488.000000</Property><Property tag='D129000' type='1'>1</Property><Property tag='D12B000' type='2'>0</Property><Property tag='D14E000' type='6'>UTC</Property><Property tag='D159000' type='6'/><Property tag='D15A000' type='6'/><Property tag='D15B000' type='6'/><Property tag='D15C000' type='6'/><Property tag='D15D000' type='1'>1</Property><Property tag='D15E000' type='1'>0</Property><Property tag='D180000' type='6'>8.8.0d39</Property><Property tag='D181000' type='6'>grub</Property><Property tag='13000000' type='1'>1</Property><Property tag='14000000' type='1'>1</Property><Property tag='14002000' type='1'>0</Property><Property tag='14004000' type='1'>0</Property><Property tag='1800B000' type='6'/><Property tag='1800C000' type='2'>0</Property><Property tag='1800D000' type='6'>VirtualBox--SN-0--MAC-08-00-27-4B-05-76</Property></PropertyBag></PropertyBags></NISysAPI_Results>"

def getIP():
	retVal = socket.gethostbyname(socket.getfqdn())
	if retVal.startswith("127."):
		# localhost's IP was returned
		# try an alternative approach
		try:
			ips = subprocess.check_output('hostname -I', shell=True)
			if len(ips) != 0:
				retVal = ips.strip().split()[0]
			else:
				print('getIP() - 1st try failed')
		except:
			print("getIP(): exception occurred with 'hostname -i':" + ips)
	if retVal.startswith("127."):
		# we still didn't get the IP
		# try an alternative that requires an internet connection
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(('8.8.8.8',80))
			retVal = s.getsockname()[0]
			s.close()
		except:
			print('getIP() - 2nd try failed')
			retVal = '0.0.0.0'
	return retVal

def restartLV():
	# Some early versions of systemd (v44) don't consistently restart
	# services, so retry a few times if the restart fails.
	print "Restarting LabVIEW now..."
	retries = 0
	while retries < RESTART_MAX_RETRIES:
		retval = os.system("/bin/systemctl restart labview.service")
		if retval == 0:
			print "Restart successful"
			return
		else:
			retries = retries + 1
			print "Restart failed; retry %d" % retries
			time.sleep(RESTART_RETRY_DELAY)

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(s):
		ppath = urlparse.urlparse(s.path)
		query = urlparse.parse_qs(ppath.query)
		if s.path.find("National%20Instruments%2FWeb%20Servers%2FNI%20System%20Web%20Server%2Fhttp") >= 0:
			# Service Locator for System Web Server; redirect to same port
			s.send_response(200)
			s.send_header("Content-type", "text/html")
			s.end_headers()
			s.wfile.write("Mapping=" + str(PORT_NUMBER) + "\r\n")
		elif s.path.find("National%20Instruments%2FNI%2DRPC%2FInterface") >= 0:
			s.send_response(200)
			s.send_header("Content-type", "text/html")
			s.end_headers()
			s.wfile.write("Mapping=0\r\n")
		elif ppath.path == '/login' and 'username' in query:
			# login challange
			s.send_response(403)
			s.send_header("X-NI-AUTH-PARAMS", "N=1,s=n7gxGBi085pJ+upFcfxEvQ==,B=ro8BaR4PUaUUcGsQZvFeE8Gbav1iYBFX3+37bGNJUCPcOSvuzle9y5EErTu4F2/Ry5GhmaYHCYo9sBbqa9HAJFk+TMc641aZlnsUG+fojWPdef98Lnis8kuXqfl5GTKgM9PS4CF+4AJ2MM59HQW6+Qm/mCZLDJhMPWr+efFmEvI=,ss=")
			s.end_headers()
		elif ppath.path == '/logout':
			# logout call
			s.send_response(200)
			s.send_header("Content-type", "text/html")
			s.send_header("Set-Cookie", "_appwebSessionId_=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
			s.end_headers()
			s.wfile.write("User admin logged out.")
		elif s.path.find("deletetree") >= 0:
			# call to service locator to remove a service
			# this happens when LV daemon shuts down
			# since the daemon might not be running when the 
			# response is sent, just close the connection
			print "GET deletetree received"
			s.wfile.close()
		elif s.path.find("publish") >= 0:
			# call to service locator to add a service
			# this happens when LV daemon starts
			s.send_response(200)
			s.end_headers()
		else:
			s.send_error(404)
			
	def do_POST(s):
		ppath = urlparse.urlparse(s.path)
		length = int(s.headers['content-length'])
		postvars = urlparse.parse_qs(s.rfile.read(length))
		if ppath.path == '/login':
			# actual login, happens after login challenge
			s.send_response(200)
			s.send_header("Content-type", "text/xml")
			s.send_header("Set-Cookie", "_appwebSessionId_=Zoz4eDPybs#qoUb9za2m0Q!!; Path=/")
			s.end_headers()
			s.wfile.write(SYSAPI_RESPONSE_LOGIN)
		elif ppath.path == '/rtexecsvc/RebootEx':
			# reboot call
			# there is form encoded data as part of this call
			# we could parse this using cgi.FieldStorage
			# details here: https://pymotw.com/2/BaseHTTPServer/
			s.send_response(202)
			s.send_header("Content-type", "text/plain")
			s.end_headers()
			s.wfile.write("Rebooting in 0 seconds")
			# spawn a daemon thread to do the reboot so the
			# HTTP Handler can send its response immediately
			t = threading.Thread(target=restartLV)
			t.setDaemon(True)
			t.start()
		elif ppath.path == '/nisysapi/server':
			# handle a request for system information
			# there can be many more requests to sysapi server
			# but for now just assume it's the most common case
			# this type of request has url-encoded form data like this:
			# Version=00010001&Plugins=nisyscfg%2cNetworkConfig&response_encoding=UTF-8&Function=SearchForItemsAndProperties&FilterMode=1&NbrBags=0&
			s.protocol_version = "HTTP/1.1"
			s.server_version = "Embedthis-http"
			s.sys_version = ""
			s.send_response(200)
			s.send_header("Keep-Alive", "timeout=60, max=199")
			s.send_header("Content-type", "text/xml; charset=utf-8")
			s.send_header("Cache-Control", "no-cache")
			s.send_header("Connection", "Keep-Alive")
			if postvars['Function'][0] == 'SearchForItemsAndProperties':
				ipAddr = getIP()
				hostname = socket.gethostname()
				respWithHostName = SYSAPI_RESPONSE_SEARCH_PROPERTIES % (ipAddr, hostname)
				s.send_header("Content-Length", str(len(respWithHostName)))
				s.end_headers()
				s.wfile.write(respWithHostName)
			elif postvars['Function'][0] == 'EnumSystemExperts':
				s.send_header("Content-Length", str(len(SYSAPI_RESPONSE_ENUM_EXPERTS)))
				s.end_headers()
				s.wfile.write(SYSAPI_RESPONSE_ENUM_EXPERTS)
			else:
				print "Unknown SysAPI Function request received"
				print postvars
				s.send_error(404)
		else:
			print "Unknown command received"
			s.send_error(404)

class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	""" Handle requests in a separate thread. """

if __name__ == '__main__':
	httpd = ThreadedHTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
	try:
		print "Starting NISysServer..."
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
