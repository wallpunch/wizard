'''
Test if can complete TLS handshakes (port 443) with an IP
address that is allowed but subject to censorship. Test:
	- Handshake without any SNI
	- An SNI known to be allowed
	- An SNI known to be blocked
	- A known blocked SNI, but with ClientHello fragmenting
'''

import ssl
import socket

from testUtils import FAMILY_VALUES,getResultIcon,getCensorsString,LogColors
from testInterface import TestGroup

SNI_TEST_STRATEGIES = ("none","allow","block","frag")

class TlsHandshaker:
	'''
	Given a connected TCP socket and a destination SNI,
	attempts to complete a TLS handshake either with or
	without ClientHello record fragmentation
	'''
	def __init__(self,logger,sock,sni):
		self.logger = logger
		self.sock = sock
		self.sniBytes = None if sni is None else sni.encode()

		self.incBio = ssl.MemoryBIO()
		self.outBio = ssl.MemoryBIO()
		context = ssl.create_default_context()
		context.check_hostname = False
		self.ssl = context.wrap_bio(
			self.incBio, self.outBio, server_side=False,
			server_hostname=sni
		)

	def tryHandshake(self,shouldFrag):
		try:
			self.ssl.do_handshake()
			return False
		except ssl.SSLWantReadError:
			pass # handshake isn't finished

		try:
			data = self.outBio.read()
			if data:
				if shouldFrag: # then SNI is not None
					data = self.splitHello(data)
				self.logger(f"Sending out {len(data)}b...")
				self.sock.send(data)
				return True
		except ssl.SSLWantReadError:
			pass # no data to send

		data = self.sock.recv(65535)
		if not data:
			raise Exception("Server closed connection")
		self.logger(f"Reading in {len(data)}b...")
		self.incBio.write(data)
		return True

	def splitHello(self,data):
		self.logger("Splitting ClientHello record on SNI")
		hdr = data[:3]
		[preSni,postSni] = data[5:].split(self.sniBytes)
		frags = [
			preSni + self.sniBytes[:3],
			self.sniBytes[3:] + postSni
		]
		outData = b""
		for f in frags:
			outData += hdr + len(f).to_bytes(2,'big') + f
		return outData

class TlsTester(TestGroup):
	'''
	A test group to assess the system's ability to
	establish TLS connections
	'''
	@staticmethod
	def getTestTag():
		return "TLS"

	@staticmethod
	def getPrereqs():
		return ["Route","TCP"]

	@staticmethod
	def getDefaultResults():
		return {
			"IPv4": False,
			"IPv6": False
		}

	def checkIfShouldSkip(self,globalResults):
		'''
		Skip if TCP test failed
		'''
		skip = True
		for family in FAMILY_VALUES:
			tcpRes = globalResults["TCP"][family]
			if (
				tcpRes is not False and # TCP test ran
				None in tcpRes[443].values() # connected to 443
			):
				self.results[family] = {}
				skip = False
		if skip:
			return "cannot make TCP connections"
		return None

	def startTest(self):
		for family in FAMILY_VALUES:
			if self.results[family] is False:
				continue # not routable
			addr = self.config["addrs"][family]
			for strategy in SNI_TEST_STRATEGIES:
				if strategy == "none":
					sni = None
				elif strategy == "allow":
					sni = self.config["snis"]["allow"]
				else: # block, frag
					sni = self.config["snis"]["block"]
				self.startTestThread(
					self.tlsThread,
					(family,addr,sni,strategy),
					f"{strategy}, {sni}",
					self.config["timeout"]
				)

	def logResults(self):
		resStr = ""
		for family, results in self.results.items():
			if results is False:
				continue
			resStr += family + ": "
			noneIcon = getResultIcon(results["none"] is None)
			resStr += f"IP-only {noneIcon} "
			allowIcon = getResultIcon(results["allow"] is None)
			resStr += f"SNI {allowIcon}\n"

			censors = []
			blockRes = results["block"]
			if blockRes is not None:
				censors.append(f"Blocked SNI handshake {blockRes}")
			resStr += getCensorsString(censors)

			fragRes = results["frag"]
			if fragRes is None:
				resStr += f"    Circumvention found: {LogColors.GREEN}TLS record fragmentation{LogColors.RESET}\n"
			else:
				resStr += f"    {LogColors.RED}TLS record fragmentation {fragRes}{LogColors.RESET}\n"
		return resStr

	@staticmethod
	def tlsThread(timeout,logger,results,family,addr,sni,strategy):
		results[family][strategy] = "timeout"

		sock = socket.socket(FAMILY_VALUES[family], socket.SOCK_STREAM)
		if timeout.is_set():
			return

		try:
			dst = (addr, 443)
			logger(f"Connecting socket to {dst}")
			sock.connect(dst)
			if timeout.is_set():
				return
		except Exception as e:
			if not timeout.is_set():
				logger(f"Connect failed with exception: {e}")
				results[family][strategy] = "error"
			return

		try:
			logger("Wrapping socket with SSL context")
			sslObj = TlsHandshaker(logger,sock,sni)
		except Exception as e:
			if not timeout.is_set():
				logger(f"SSL wrap failed with exception: {e}")
				results[family][strategy] = "error"
			return

		errMsg = None
		try:
			logger("Attempting TLS handshake")
			shouldFrag = strategy == "frag"
			# loop until ssl wrapper reports handshake complete
			while sslObj.tryHandshake(shouldFrag):
				if timeout.is_set():
					return
		except ssl.SSLError as e:
			# Since we are using a spoofed SNI, the server
			# will always send a failure alert record if our
			# handshake makes it through successfully
			# (So for test purposes this means success)
			if e.reason != "SSLV3_ALERT_HANDSHAKE_FAILURE":
				errMsg = str(e)
		except Exception as e:
			errMsg = str(e)

		if timeout.is_set():
			return
		if errMsg is None:
			logger("TLS handshake complete!")
			results[family][strategy] = None
		else:
			logger(f"TLS handshake failed with error: {errMsg}")
			results[family][strategy] = "error"


def getClientTests():
	return [TlsTester]
