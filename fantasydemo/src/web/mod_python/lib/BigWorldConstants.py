# BigWorld web mod_python integration constants

import os

UID = 605 # change to the UID you are running your server as

# Get the correct HOME for UID
pipe = os.popen( "getent passwd %d" % UID, "r" )
contents = pipe.read()
HOME = contents.split( ":" )[5]
pipe.close()

LOGIN_PAGE 		= 'Login'
WELCOME_PAGE	= 'Welcome'
CHARACTERS_PAGE	= 'Characters'

MAX_INACTIVITY_TIMEOUT = 1800 # seconds (30 minutes)

FD_PYTHON_SRC_ROOT = os.path.join( os.path.dirname( __file__ ), ".." )
ITEMS_DEF_PATH = os.path.join( FD_PYTHON_SRC_ROOT, "data/items.xml" )
ITEMS_IMAGE_ROOT = "images/items"

# BigWorldConstants.py
