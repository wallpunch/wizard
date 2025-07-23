'''
For IPv4+6 versions of TCP and UDP, see if:
	1) We can create a socket
	2) The system can route to a non-local address
'''

import socket
from testUtils import FAMILY_VALUES,PROTOCOL_VALUES,getResultIcon
from testInterface import TestGroup

ROUTE_TEST_DGRAM = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'

class RouteTester(TestGroup):
	'''
	A test group to assess the system's routing capability
	'''
	@staticmethod
	def getTestTag():
		return "Route"

	@staticmethod
	def getDefaultResults():
		return {
			"IPv4": {
				"TCP": False,
				"UDP": False
			},
			"IPv6": {
				"TCP": False,
				"UDP": False
			}
		}

	def startTest(self):
		for family in FAMILY_VALUES:
			for protocol in PROTOCOL_VALUES:
				dst = (self.config["addrs"][family], self.config["port"])
				self.startTestThread(
					self.routeThread,
					(family,protocol,dst),
					f"{family}, {protocol}",
					self.config["timeout"]
				)

	def logResults(self):
		resStr = ""
		for family in FAMILY_VALUES:
			resStr += family + ": "
			for protocol in PROTOCOL_VALUES:
				if self.results[family][protocol]:
					resIcon = getResultIcon(True)
				else:
					resIcon = getResultIcon(False)
				resStr += f"{protocol} {resIcon} "
			resStr += "\n"
		return resStr

	@staticmethod
	def routeThread(timeout,logger,results,family,protocol,dst):
		try:
			logger("Creating socket...")
			sock = socket.socket(FAMILY_VALUES[family], PROTOCOL_VALUES[protocol])
			sock.settimeout(0.001)
			if timeout.is_set():
				return

			if protocol == "TCP":
				logger(f"Connecting socket to {dst}")
				sock.connect(dst)
			elif protocol == "UDP":
				logger(f"Sending datagram to {dst}")
				sock.sendto(ROUTE_TEST_DGRAM, dst)
			sock.close()
		except socket.timeout:
			pass # for test purposes conn timeout means routable
		except Exception as e:
			if not timeout.is_set():
				logger(f"Failed with exception: {e}")
			return
		logger("Routing successful!")
		results[family][protocol] = True


def getClientTests():
	return [RouteTester]
