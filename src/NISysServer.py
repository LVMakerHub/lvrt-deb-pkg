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
		elif ppath.path == '/deletetree':
			# call to service locator to remove a service
			# this happens when LV daemon shuts down
			# since the daemon might not be running when the 
			# response is sent, just close the connection
			print "GET deletetree received"
			s.wfile.close()
		elif ppath.path == '/publish':
			# call to service locator to add a service
			# this happens when LV daemon starts
			s.send_response(200)
			s.end_headers()
		else:
			s.send_error(404)
			
	def do_POST(s):
		ppath = urlparse.urlparse(s.path)
		query = urlparse.parse_qs(ppath.query)
		if ppath.path == '/login':
			# actual login, happens after login challenge
			s.send_response(200)
			s.send_header("Content-type", "text/xml")
			s.send_header("Set-Cookie", "_appwebSessionId_=Zoz4eDPybs#qoUb9za2m0Q!!; Path=/")
			s.end_headers()
			loginxmldata = "<?xml version='1.0' encoding='UTF-8'?><Permissions><Permission><Name>GetDB</Name><BuiltIn>false</BuiltIn><ID>0</ID></Permission><Permission><Name>SetDB</Name><BuiltIn>false</BuiltIn><ID>1</ID></Permission><Permission><Name>FSRead</Name><BuiltIn>false</BuiltIn><ID>2</ID></Permission><Permission><Name>FSWrite</Name><BuiltIn>false</BuiltIn><ID>3</ID></Permission><Permission><Name>SSLAdminModifyCerts</Name><BuiltIn>false</BuiltIn><ID>4</ID></Permission><Permission><Name>SSLAdminReadCerts</Name><BuiltIn>false</BuiltIn><ID>5</ID></Permission><Permission><Name>NIWebCer</Name><BuiltIn>false</BuiltIn><ID>6</ID></Permission><Permission><Name>GetWSAPIKey</Name><BuiltIn>false</BuiltIn><ID>7</ID></Permission><Permission><Name>ManageWS</Name><BuiltIn>false</BuiltIn><ID>8</ID></Permission><Permission><Name>SetWSAPIKey</Name><BuiltIn>false</BuiltIn><ID>9</ID></Permission><Permission><Name>WIFConfigureAppServer</Name><BuiltIn>false</BuiltIn><ID>10</ID></Permission><Permission><Name>GetSystemConfiguration</Name><BuiltIn>false</BuiltIn><ID>11</ID></Permission><Permission><Name>SetSystemConfiguration</Name><BuiltIn>false</BuiltIn><ID>12</ID></Permission><Permission><Name>FirmwareUpdate</Name><BuiltIn>false</BuiltIn><ID>13</ID></Permission><Permission><Name>Reboot</Name><BuiltIn>false</BuiltIn><ID>14</ID></Permission><Permission><Name>RemoteShell</Name><BuiltIn>false</BuiltIn><ID>15</ID></Permission><Permission><Name>SetRTLockPassword</Name><BuiltIn>false</BuiltIn><ID>16</ID></Permission><Permission><Name>ViewConsoleOutput</Name><BuiltIn>false</BuiltIn><ID>17</ID></Permission><Permission><Name>GetSyslog</Name><BuiltIn>false</BuiltIn><ID>18</ID></Permission><Permission><Name>ManageExtensions</Name><BuiltIn>false</BuiltIn><ID>19</ID></Permission></Permissions>"
			s.wfile.write(loginxmldata)
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
			s.send_response(200)
			s.send_header("Content-type", "text/xml; charset=utf-8")
			s.end_headers()
			ipAddr = getIP()
			hostname = socket.gethostname()
			sysapixmldata = "<?xml version='1.0' encoding='utf-8'?><NISysAPI_Results hr='0' version='00010001'><PropertyBags><PropertyBag><Property tag='1000000' type='6'>//localhost/nisyscfg/usb0</Property><Property tag='1001000' type='1'>0</Property><Property tag='1009000' type='1'>0</Property><Property tag='100D000' type='3'>0</Property><Property tag='101C000' type='2'>1</Property><Property tag='101D000' type='6'>usb0</Property><Property tag='101E000' type='6'>nisyscfg</Property><Property tag='101F000' type='6'>Ethernet Adapter usb0</Property><Property tag='1020000' type='1'>0</Property><Property tag='1022000' type='5'>{00000000-0000-0000-0000-000000000000}</Property><Property tag='1028000' type='1'>0</Property><Property tag='102A000' type='2'>1000</Property><Property tag='1037000' type='3'>983040</Property><Property tag='1038000' type='1'>1</Property><Property tag='1039000' type='2'>1</Property><Property tag='103A000' type='3'>5</Property><Property tag='1054000' type='1'>0</Property><Property tag='D102000' type='3'>2</Property><Property tag='D103000' type='3'>2</Property><Property tag='D104000' type='6'>00:80:2F:21:2F:99</Property><Property tag='D105000' type='3'>8</Property><Property tag='D106000' type='3'>8</Property><Property tag='D107000' type='6'>0.0.0.0</Property><Property tag='D108000' type='3'>1</Property><Property tag='D109000' type='6'>0.0.0.0</Property><Property tag='D10A000' type='6'>0.0.0.0</Property><Property tag='D10B000' type='6'>0.0.0.0</Property><Property tag='D10F000' type='3'>1</Property><Property tag='D110000' type='3'>1</Property><Property tag='D111000' type='3'>1</Property><Property tag='D119000' type='3'>1</Property><Property tag='D11A000' type='3'>1</Property><Property tag='D126000' type='1'>0</Property><Property tag='D12C000' type='3'>1</Property></PropertyBag><PropertyBag><Property tag='1000000' type='6'>//localhost/nisyscfg/eth0</Property><Property tag='1001000' type='1'>0</Property><Property tag='1009000' type='1'>0</Property><Property tag='100D000' type='3'>0</Property><Property tag='101C000' type='2'>1</Property><Property tag='101D000' type='6'>eth0</Property><Property tag='101E000' type='6'>nisyscfg</Property><Property tag='101F000' type='6'>Ethernet Adapter eth0</Property><Property tag='1020000' type='1'>0</Property><Property tag='1022000' type='5'>{00000000-0000-0000-0000-000000000000}</Property><Property tag='1028000' type='1'>0</Property><Property tag='102A000' type='2'>1000</Property><Property tag='1037000' type='3'>983040</Property><Property tag='1038000' type='1'>1</Property><Property tag='1039000' type='2'>1</Property><Property tag='103A000' type='3'>5</Property><Property tag='1054000' type='1'>0</Property><Property tag='D102000' type='3'>2</Property><Property tag='D103000' type='3'>2</Property><Property tag='D104000' type='6'>00:80:2F:21:2F:97</Property><Property tag='D105000' type='3'>2</Property><Property tag='D106000' type='3'>15</Property><Property tag='D107000' type='6'>%s</Property><Property tag='D108000' type='3'>1</Property><Property tag='D109000' type='6'>255.255.254.0</Property><Property tag='D10A000' type='6'>10.2.106.1</Property><Property tag='D10B000' type='6'>130.164.12.8</Property><Property tag='D10F000' type='3'>1</Property><Property tag='D110000' type='3'>95</Property><Property tag='D111000' type='3'>64</Property><Property tag='D119000' type='3'>1</Property><Property tag='D11A000' type='3'>1</Property><Property tag='D126000' type='1'>1</Property><Property tag='D12C000' type='3'>1</Property></PropertyBag><PropertyBag><Property tag='1000000' type='6'>//localhost/nisyscfg/eth1</Property><Property tag='1001000' type='1'>0</Property><Property tag='1009000' type='1'>0</Property><Property tag='100D000' type='3'>0</Property><Property tag='101C000' type='2'>1</Property><Property tag='101D000' type='6'>eth1</Property><Property tag='101E000' type='6'>nisyscfg</Property><Property tag='101F000' type='6'>Ethernet Adapter eth1</Property><Property tag='1020000' type='1'>0</Property><Property tag='1022000' type='5'>{00000000-0000-0000-0000-000000000000}</Property><Property tag='1028000' type='1'>0</Property><Property tag='102A000' type='2'>1000</Property><Property tag='1037000' type='3'>983040</Property><Property tag='1038000' type='1'>1</Property><Property tag='1039000' type='2'>1</Property><Property tag='103A000' type='3'>5</Property><Property tag='1054000' type='1'>0</Property><Property tag='D102000' type='3'>2</Property><Property tag='D103000' type='3'>3</Property><Property tag='D104000' type='6'>00:80:2F:21:2F:98</Property><Property tag='D105000' type='3'>2</Property><Property tag='D106000' type='3'>15</Property><Property tag='D107000' type='6'>0.0.0.0</Property><Property tag='D108000' type='3'>1</Property><Property tag='D109000' type='6'>0.0.0.0</Property><Property tag='D10A000' type='6'>0.0.0.0</Property><Property tag='D10B000' type='6'>0.0.0.0</Property><Property tag='D10F000' type='3'>1</Property><Property tag='D110000' type='3'>95</Property><Property tag='D111000' type='3'>0</Property><Property tag='D119000' type='3'>1</Property><Property tag='D11A000' type='3'>1</Property><Property tag='D126000' type='1'>0</Property><Property tag='D12C000' type='3'>1</Property></PropertyBag><PropertyBag><Property tag='1000000' type='6'>//localhost/nisyscfg/system</Property><Property tag='1001000' type='1'>1</Property><Property tag='1002000' type='3'>0</Property><Property tag='1004000' type='6'>National Instruments</Property><Property tag='1005000' type='3'>30549</Property><Property tag='1006000' type='6'>LINX Target</Property><Property tag='1007000' type='6'>01A549AB</Property><Property tag='1008000' type='1'>1</Property><Property tag='1009000' type='1'>0</Property><Property tag='100D000' type='3'>0</Property><Property tag='101C000' type='2'>1</Property><Property tag='101D000' type='6'>system</Property><Property tag='101E000' type='6'>nisyscfg</Property><Property tag='101F000' type='6'>%s</Property><Property tag='1020000' type='1'>0</Property><Property tag='1022000' type='5'>{00000000-0000-0000-0000-000000000000}</Property><Property tag='1024000' type='2'>1</Property><Property tag='1028000' type='1'>0</Property><Property tag='102A000' type='2'>1000</Property><Property tag='102F000' type='6'>3.0.0f0</Property><Property tag='1033000' type='6'>00:80:2F:21:2F:97</Property><Property tag='1037000' type='3'>983040</Property><Property tag='1038000' type='1'>1</Property><Property tag='1039000' type='2'>1</Property><Property tag='103A000' type='3'>4</Property><Property tag='103C000' type='6'>cRIO</Property><Property tag='103D000' type='6' /><Property tag='104A000' type='1'>1</Property><Property tag='104B000' type='6'>*.cfg</Property><Property tag='104C000' type='2'>0</Property><Property tag='104E000' type='6'>NI-Linux x64</Property><Property tag='104F000' type='6'>3.14.40-rt37-3.0.0f1</Property><Property tag='1050000' type='6'>NI Linux Real-Time x64 3.14.40-rt37-3.0.0f1</Property><Property tag='1051000' type='7'>9B613800 E2CD41C9 D246A77B 0</Property><Property tag='1052000' type='1'>0</Property><Property tag='1053000' type='6'>Running</Property><Property tag='1054000' type='1'>0</Property><Property tag='1058000' type='2'>2</Property><Property tag='5105000' type='1'>0</Property><Property tag='D11D000' type='6'>en</Property><Property tag='D11E000' type='6'>en</Property><Property tag='D120000' type='6'>CUT0</Property><Property tag='D122000' type='4'>3522608.000000</Property><Property tag='D123000' type='4'>3070516.000000</Property><Property tag='D129000' type='1'>1</Property><Property tag='D12B000' type='2'>0</Property><Property tag='D14E000' type='6'>UTC</Property><Property tag='D159000' type='6' /><Property tag='D15A000' type='6' /><Property tag='D15B000' type='6' /><Property tag='D15C000' type='6' /><Property tag='D15D000' type='1'>1</Property><Property tag='D15E000' type='1'>0</Property><Property tag='D15F000' type='1'>0</Property><Property tag='13000000' type='1'>1</Property><Property tag='14000000' type='1'>0</Property><Property tag='14002000' type='1'>0</Property><Property tag='14004000' type='1'>0</Property></PropertyBag></PropertyBags></NISysAPI_Results>"
			s.wfile.write(sysapixmldata % (ipAddr, hostname))
		else:
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
