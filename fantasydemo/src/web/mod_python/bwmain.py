"""
Module specified as the mod_python PythonHandler.
"""
from mod_python import apache, util

import re
import sys
import imp

import logging
import traceback

log = logging.getLogger( "fd_python.bwmain" )


def handler( req ):
	"""
	The handler function required by mod_python. This is the entry point for
	our request processing.
	"""

	log.info( "********* bwmain.py: handler started *********" )
	log.debug( "URI: %s", req.unparsed_uri )
	# figure out which page users want from the URI
	# import it and instantiate it
	pageNameRe = re.search( '([^/]+)\.[a-z]+$', req.uri )
	if pageNameRe == None:
		req.write( "Could not get pattern from %s" % req.uri )
		# this should be 404 file not found
		log.info( 'bwmain.py: handler finished - returning HTTP_NOT_FOUND' )
		return apache.HTTP_NOT_FOUND

	pageName = pageNameRe.groups()[0]

	# try to import the module with the same name as the
	# page requested
	fp, path, description = imp.find_module( pageName )

	try:
		pageMod = imp.load_module( pageName, fp, path, description )
	finally:
		if fp != None:
			fp.close()

	# reload the page - in production you should remove this line as it will be
	# slow per page view
	reload( pageMod )

	# we have a page module - now try instantiating and rendering it

	pageClass = getattr( pageMod, pageName )

	code = apache.HTTP_INTERNAL_SERVER_ERROR
	try:
		page = pageClass( req )
		code = page.render()
	except apache.SERVER_RETURN, e:
		if e.args[0] == apache.OK:
			# the exception was a result of a redirect, just raise it and we're
			# done
			raise e
		else:
			log.error( traceback.format_exc() )
			code = apache.HTTP_INTERNAL_SERVER_ERROR
	except:
		log.info( "general error" )
		log.error( traceback.format_exc() )
		code = apache.HTTP_INTERNAL_SERVER_ERROR

	return code


# Set up logging handler on import of this module
rootLog = logging.getLogger()
rootLog.setLevel( logging.DEBUG )

logFormatter = logging.Formatter( "%(asctime)s %(process)-6d %(levelname)-8s "
	"%(name)s %(message)s" )

streamHandler = logging.StreamHandler()
streamHandler.setFormatter( logFormatter )
streamHandler.setLevel( logging.DEBUG )
rootLog.addHandler( streamHandler )

# bwmain.py
