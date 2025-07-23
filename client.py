'''
Circumvention Wizard (Client)

Runs on a client device. Assesses the device's internet
connectivity, checks for signs of internet censorship,
and tests corresponding circumvention methods.
'''

import json
import pkgutil
import importlib

from testUtils import printHeader

TEST_PACKAGE_DIR = "tests"

def loadAllTests(globalConfig):
	tests = []
	for _importer,modName,_ispkg in pkgutil.iter_modules([TEST_PACKAGE_DIR]):
		module = importlib.import_module(f"{TEST_PACKAGE_DIR}.{modName}")
		if not hasattr(module,"getClientTests"):
			continue
		for testCls in module.getClientTests():
			if testCls.getTestTag() in globalConfig:
				tests.append(testCls)
	return tests

def getNextTest(todoTests,doneTests):
	for testCls in todoTests:
		allPrereqsDone = True
		for testTag in testCls.getPrereqs():
			if testTag not in doneTests:
				allPrereqsDone = False
				break
		if allPrereqsDone:
			return testCls
	return None

def runTests():
	globalConfig = None
	with open("config.json", "r") as f:
		globalConfig = json.load(f)
	globalResults = {}

	todoTests = loadAllTests(globalConfig)
	print(
		f"Loaded {len(todoTests)} tests: "
		+ " ".join(t.getTestTag() for t in todoTests)
	)

	doneTests = []
	while todoTests:
		testCls = getNextTest(todoTests,doneTests)
		testGroup = testCls(globalConfig,globalResults)
		testTag = testGroup.getTestTag()
		printHeader(f"{testTag} Test",False)
		if testGroup.skipReason is None:
			testTime,testResults = testGroup.runTest()
			printHeader(f"{testTag} Results: (done in {testTime}s)",True)
			print(testResults)
		else:
			print(f"Test skipped because {testGroup.skipReason}")
		todoTests.remove(testCls)
		doneTests.append(testTag)
	print("All tests complete!")

if __name__ == "__main__":
	runTests()
