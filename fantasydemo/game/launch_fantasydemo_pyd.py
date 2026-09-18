# This python file sets up the system paths and launches fantasydemo.pyd.

import sys
import os

# Add the client scripts to the path.
fantasydemoPaths = [os.path.normpath( os.path.join( os.getcwd(), r'..\res\scripts\client' ) ),
					os.path.normpath( os.path.join( os.getcwd(), r'..\res\scripts\common' ) ),
					os.path.normpath( os.path.join( os.getcwd(), r'..\..\bigworld\res\scripts\client' ) ),
					os.path.normpath( os.path.join( os.getcwd(), r'..\..\bigworld\res\scripts\common' ) ),]

sys.path[1:1] =	fantasydemoPaths


# run the client. Replace fantasydemo with
# the name of your extension module (.pyd)
import fantasydemo

def quoteArg(s):
	if ' ' in s:
		s = s.replace(r'"', r'\"')
		if s[-1] == '\\': s = s + '\\'
		return '"' + s  + '"'
	else:
		return s

fantasydemo.run(' '.join( [ quoteArg(x) for x in sys.argv] ))
