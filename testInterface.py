'''
Defines the interface test modules must follow
'''

from time import monotonic
import threading

class TestThread:
	'''
	A single test that should be run in its own thread and
	preempted when its timeout is reached
	'''
	def __init__(self,func,args,logHdr,timeout,results):
		self.logHdr = logHdr
		self.log("Starting test...")

		self.timeoutEvent = threading.Event()
		self.thread = threading.Thread(
			target=func, daemon=True,
			args=(self.timeoutEvent,self.log,results,*args)
		)
		self.thread.start()
		self.cutoff = monotonic() + timeout

	def log(self,s):
		print(self.logHdr + s)

	def join(self):
		waitTime = max(0, self.cutoff - monotonic())
		self.thread.join(timeout=waitTime)
		self.timeoutEvent.set()
		if self.thread.is_alive():
			self.log("Test timed out!")


class TestGroup:
	'''
	A group of related tests that can be run in parallel.
	'''
	def __init__(self,globalConfig,globalResults):
		self.startTime = monotonic()
		testTag = self.getTestTag()
		self.config = globalConfig[testTag]
		self.threads = []

		self.results = self.getDefaultResults()
		globalResults[testTag] = self.results
		self.skipReason = self.checkIfShouldSkip(globalResults)

	@staticmethod
	def getTestTag():
		'''
		Return a string identifying this test group
		'''
		return ""

	@staticmethod
	def getPrereqs():
		'''
		Return the tags of other tests this test relies on
		'''
		return []

	@staticmethod
	def getDefaultResults():
		'''
		Return this test's default (i.e. all failed) results
		'''
		return {}

	def checkIfShouldSkip(self,globalResults):
		'''
		If earlier results indicate this test shouldn't be run
		return a string indicating why (otherwise return None)
		'''
		return None

	def runTest(self):
		'''
		Wait for all running test threads to complete or
		timeout, then log the results and return a summary.
		'''
		self.startTest()
		for t in sorted(self.threads, key=lambda t: t.cutoff):
			t.join()
		testResults = self.logResults()
		testTime = round(monotonic() - self.startTime, 3)
		return testTime,testResults

	def startTest(self):
		'''
		Implemented by subclasses to create the test threads
		'''
		pass

	def startTestThread(self,func,args,logTag,timeout):
		'''
		Create a new test thread in this test group
		'''
		threadIdx = len(self.threads)
		logHdr = f"{self.getTestTag()} #{threadIdx} ({logTag}): "
		self.threads.append(TestThread(
			func, args, logHdr, timeout, self.results
		))

	def logResults(self):
		'''
		Log the results of the completed test threads and
		return a string summarizing the results.
		'''
		return ""

def getClientTests():
	'''
	Return a list of TestGroup classes defined in this
	module that clients should run
	'''
	return []
