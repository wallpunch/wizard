'''
Various utility functions shared by tests
'''

import socket

# Linking socket constants to human-readable strings
FAMILY_VALUES = {
	"IPv4": socket.AF_INET,
	"IPv6": socket.AF_INET6
}
PROTOCOL_VALUES = {
	"TCP": socket.SOCK_STREAM,
	"UDP": socket.SOCK_DGRAM
}

class LogColors:
	'''
	ANSI color codes for pretty terminal output
	'''
	RESET = '\033[0m'
	RED = '\033[91m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	BLUE = '\033[94m'
	MAGENTA = '\033[95m'
	CYAN = '\033[96m'
	WHITE = '\033[97m'

DISPLAY_WIDTH = 50
def printHeader(title,isRes): # test start, test res
	sep = "\n" + ('=' * DISPLAY_WIDTH) + "\n"
	print(
		(LogColors.MAGENTA if isRes else LogColors.CYAN)
		+ sep + title.center(DISPLAY_WIDTH) + sep
		+ LogColors.RESET
	)

def getResultIcon(success,infoStr=None):
	if success is True:
		resColor = LogColors.GREEN
		resIcon = "✔"
	elif success is False:
		resColor = LogColors.RED
		resIcon = "✖"
	else: # test inconclusive
		resColor = LogColors.YELLOW
		resIcon = "?"
	if infoStr is not None:
		resIcon += " " + infoStr
	return f"({resColor}{resIcon}{LogColors.RESET})"

def getCensorsString(censors):
	resStr = ""
	if censors:
		for c in censors:
			resStr += f"    Censorship detected: {LogColors.RED}{c}{LogColors.RESET}\n"
	else:
		resStr += "    No censorship detected\n"
	return resStr
