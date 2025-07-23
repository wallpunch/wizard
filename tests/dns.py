'''
Using the system's DNS resolver, try resolving both
allowed and blocked hostnames.

Also test blocked hostnames for DNS cache poisoning by
trying to resolve a long, random (nonexisting) subdomain
'''

import socket
import random
import string

from testUtils import FAMILY_VALUES,getResultIcon,getCensorsString
from testInterface import TestGroup


class DnsTester(TestGroup):
	'''
	A test group to assess the system's DNS resolver
	'''
	@staticmethod
	def getTestTag():
		return "DNS"

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
		Skip this test if all routing tests failed
		'''
		skip = True
		for family in FAMILY_VALUES:
			if True in globalResults["Route"][family].values():
				self.results[family] = {}
				skip = False
		if skip:
			return "no routable networks"
		return None

	def startTest(self):
		self.testPrefix = "".join(random.choice(
			string.ascii_lowercase + string.digits
		) for _ in range(random.randint(40,60))) + "."
		print(f"Using POISON test prefix: {self.testPrefix}")

		for family in FAMILY_VALUES:
			if self.results[family] is False:
				continue # not routable
			for host in self.config["allow"]:
				self.startResolveTest(host,family,False)
			for host in self.config["block"]:
				self.startResolveTest(host,family,True)

	def startResolveTest(self,host,family,testPoison):
		testPrefs = [""]
		if testPoison:
			testPrefs.append(self.testPrefix)
		for prefix in testPrefs:
			self.startTestThread(
				self.resolveThread,
				(family,prefix+host),
				f"{family}, {host}" + (", POISON" if prefix else ""),
				self.config["timeout"]
			)

	def logResults(self):
		resStr = ""
		for family, results in self.results.items():
			if results is False:
				continue
			self.results[family] = True
			allowList = self.config["allow"]
			allowOkCnt = sum(results[host] for host in allowList)
			allowTotal = len(allowList)
			if allowOkCnt == allowTotal: # DNS can resolve
				resIcon = getResultIcon(True)
			elif allowOkCnt == 0: # DNS can't resolve
				resIcon = getResultIcon(False)
				self.results[family] = False
			else: # test inconclusive
				resIcon = getResultIcon(None,f"resolved {allowOkCnt}/{allowTotal}")
			resStr += f"{family}: DNS {resIcon}\n"

			censors = []
			blockList = self.config["block"]
			blockOkCnt = sum(results[host] for host in blockList)
			blockTotal = len(blockList)
			if blockOkCnt < blockTotal:
				censors.append(f"DNS blocking: {blockTotal - blockOkCnt}/{blockTotal} blocked")

			blockPoisonCnt = sum(results[self.testPrefix + host] for host in blockList)
			if blockPoisonCnt > 0:
				censors.append(f"DNS poisoning: {blockPoisonCnt}/{blockTotal} poisoned")
			resStr += getCensorsString(censors)
		return resStr

	@staticmethod
	def resolveThread(timeout,logger,results,family,host):
		results[family][host] = 0 # default to failed
		try:
			res = socket.getaddrinfo(host, None, FAMILY_VALUES[family])
			if not timeout.is_set():
				logger(f"Got {len(res)} records")
				results[family][host] = 1
		except socket.gaierror as e:
			if not timeout.is_set():
				logger(f"Failed with socket.gaierror: {e}")


def getClientTests():
	return [DnsTester]
