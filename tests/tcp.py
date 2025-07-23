'''
Test if can complete TCP handshakes (ports 80+443) with:
	- IPs known to be allowed
	- IPs known to be blocked
'''

import socket
from testUtils import FAMILY_VALUES,getResultIcon,getCensorsString
from testInterface import TestGroup


class TcpTester(TestGroup):
	'''
	A test group to assess the system's ability to establish
	TCP connections
	'''
	@staticmethod
	def getTestTag():
		return "TCP"

	@staticmethod
	def getPrereqs():
		return ["Route"]

	@staticmethod
	def getDefaultResults():
		return {
			"IPv4": False,
			"IPv6": False
		}

	def checkIfShouldSkip(self,globalResults):
		'''
		Skip if TCP routing tests all failed
		'''
		skip = True
		for family in FAMILY_VALUES:
			if globalResults["Route"][family]["TCP"]:
				self.results[family] = {}
				skip = False
		if skip:
			return "no routable TCP networks"
		return None

	def startTest(self):
		for family in FAMILY_VALUES:
			if self.results[family] is False:
				continue # not routable
			for port in self.config["ports"]:
				self.results[family][port] = {}
				addrs = self.config["addrs"][family]
				for key in ("allow","block"):
					for addr in addrs[key]:
						self.startTestThread(
							self.tcpThread,
							(family,port,addr),
							f"{key}, {addr}:{port}",
							self.config["timeout"]
						)

	def logResults(self):
		resStr = ""
		for family, portRes in self.results.items():
			if portRes is False:
				continue
			resStr += family + ": "
			censors = []
			addrs = self.config["addrs"][family]
			for port, results in portRes.items():
				dstTag = f"TCP:{port}"
				allowList = addrs["allow"]
				allowOkCnt = sum(
					(1 if results[addr] is None else 0)
					for addr in allowList
				)
				allowTotal = len(allowList)
				if allowOkCnt == allowTotal: # DNS can resolve
					resIcon = getResultIcon(True)
				elif allowOkCnt == 0: # DNS can't resolve
					resIcon = getResultIcon(False)
				else: # test inconclusive
					resIcon = getResultIcon(None,f"connected {allowOkCnt}/{allowTotal}")
				resStr += f"{dstTag} {resIcon} "

				blockList = addrs["block"]
				blocksTotal = len(blockList)

				timeoutCnt = sum(
					(1 if results[addr] == "timeout" else 0)
					for addr in blockList
				)
				if timeoutCnt > 0:
					censors.append(f"Blocked {dstTag} handshake timeouts: {timeoutCnt}/{blocksTotal} timeouts")

				errorCnt = sum(
					(1 if results[addr] == "error" else 0)
					for addr in blockList
				)
				if errorCnt > 0:
					censors.append(f"Blocked {dstTag} handshake errors: {errorCnt}/{blocksTotal} errors")
			resStr += "\n" + getCensorsString(censors)
		return resStr

	@staticmethod
	def tcpThread(timeout,logger,results,family,port,addr):
		results[family][port][addr] = "timeout"

		sock = socket.socket(FAMILY_VALUES[family], socket.SOCK_STREAM)
		if timeout.is_set():
			return

		try:
			dst = (addr, port)
			logger(f"Connecting socket to {dst}")
			sock.connect(dst)
			if timeout.is_set():
				return
		except Exception as e:
			if not timeout.is_set():
				logger(f"Failed with exception: {e}")
				results[family][port][addr] = "error"
			return
		logger("Connected!")
		results[family][port][addr] = None


def getClientTests():
	return [TcpTester]
